# -*- coding: utf-8 -*-
import json
import os.path
from typing import Union

from kubernetes import client, config
import yaml

from chaostoolkit.types import MicroservicesStatus


def all_microservices_healthy(ns: str = "default") -> MicroservicesStatus:
    """
    Check all microservices in the system are running and available.

    Returns two sequences, the first one made of non-running microservices and
    the second one made of failed services. When the system is healthy, those
    two sequences should be empty.
    """
    config.load_kube_config()
    not_ready = []
    failed = []

    v1 = client.CoreV1Api()
    ret = v1.list_namespaced_pod(namespace=ns)
    for p in ret.items:
        phase = p.status.phase
        if phase == "Failed":
            failed.append(p)
        elif phase != "Running":
            not_ready.append(p)

    return not_ready, failed


def microservice_available_and_healthy(
        name: str, ns: str = "default") -> Union[bool, None]:
    """
    Lookup a deployment with a `service` label set to the given `name` in
    the specified `ns`. Returns `True` if all found deployments have reached
    the desired number of available replicas.
    """
    config.load_kube_config()

    v1 = client.AppsV1beta1Api()
    ret = v1.list_namespaced_deployment(
        ns, label_selector="service={name}".format(name=name))

    if not ret.items:
        return None

    for d in ret.items:
        if d.status.available_replicas != d.spec.replicas:
            return False

    return True


def microservice_is_not_available(name: str, ns: str = "default") -> bool:
    """
    Lookup a deployment with a `service` label set to the given `name` in
    the specified `ns`. Returns `False` if no deployment could be found with
    said label.
    """
    config.load_kube_config()

    v1 = client.AppsV1beta1Api()
    ret = v1.list_namespaced_deployment(
        ns, label_selector="service={name}".format(name=name))

    if ret.items:
        return False

    return True


def kill_microservice(name: str, ns: str = "default"):
    """
    Kill a microservice by `name` in the namespace `ns`.

    The microservice is killed by deleting the deployment for it without
    a graceful period to trigger an abrupt termination.

    To work, the deployment must have a `service` label matching the
    `name` of the microservice.
    """
    config.load_kube_config()

    v1 = client.AppsV1beta1Api()
    ret = v1.list_namespaced_deployment(
        ns, label_selector="service={name}".format(name=name))

    body = client.V1DeleteOptions()
    for d in ret.items:
        res = v1.delete_namespaced_deployment(
            d.metadata.name, ns, body)

    v1 = client.ExtensionsV1beta1Api()
    ret = v1.list_namespaced_replica_set(
        ns, label_selector="service={name}".format(name=name))

    body = client.V1DeleteOptions()
    for r in ret.items:
        res = v1.delete_namespaced_replica_set(
            r.metadata.name, ns, body)

    v1 = client.CoreV1Api()
    ret = v1.list_namespaced_pod(
        ns, label_selector="service={name}".format(name=name))

    body = client.V1DeleteOptions()
    for p in ret.items:
        res = v1.delete_namespaced_pod(
            p.metadata.name, ns, body)


def start_microservice(deployment_config: str, ns: str = "default"):
    """
    Start a microservice described by the deployment config, which must be the
    path to the JSON or YAML representation of the deployment.
    """
    config.load_kube_config()

    with open(deployment_config) as f:
        p, ext = os.path.splitext(deployment_config)
        if ext == '.json':
            deployment = json.loads(f.read())
        elif ext in ['.yml', '.yaml']:
            deployment = yaml.load(f.read())
        else:
            raise IOError(
                "cannot process {path}".format(path=deployment_config))

    v1 = client.AppsV1beta1Api()
    resp = v1.create_namespaced_deployment(ns, body=deployment)
    return resp
