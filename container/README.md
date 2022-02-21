# Chaos Toolkit container image

This  directory contains two container image templates:

* One to build a basic image with Chaos Toolkit only. Based on debian Bullseye.
* One to build a full image with Chaos Toolkit and many dependencies 
  Based on debian Bullseye.

They differ from the `chaostoolkit/chaostoolkit` image which was build from
Alpine. Unfortunately, it's not always the best base image hence this new
`chaostoolkit/chaostoolkit-basic` image.

These images are rebuilt whenever the `chaostoolkit` CLI is released.