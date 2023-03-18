# Longhorn PVC Samba Share

Make all longhorn PVC accessible with a samba container.

## WIP!!

Possible Problems we have different namespaces for our PVC but can only start one pod for the samba port

Maybe not an problem with Kubernetes `v1.26+` see https://kubernetes.io/docs/concepts/storage/persistent-volumes/#cross-namespace-data-sources.
