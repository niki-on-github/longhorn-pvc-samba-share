import logging
import os
import sys
import time
import yaml
import tempfile

# from kubernetes import client, config


class SambaServerDeployment:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        volumes_config_path = os.getenv('VOLUMES_CONFIG_PATH', '/config/volumes.yaml')
        self.deployment_name = "longhorn-pvc-samba-server"
        self.deployment_namespace = os.getenv('NAMESPACE', "default")
        self.logger.info("VOLUMES_CONFIG_PATH=%s", volumes_config_path)
        self.logger.info("NAMESPACE=%s", self.deployment_namespace)
        self._load_config(volumes_config_path)
        # config.load_kube_config()
        # self.apps_v1 = client.AppsV1Api()


    def _wait_start_delay(self) -> None:
        start_delay_in_seconds = int(str(os.getenv('START_DELAY_IN_SECONDS', 0)))
        if start_delay_in_seconds > 0:
            self.logger.info('Wait %d seconds', start_delay_in_seconds)
            time.sleep(start_delay_in_seconds)


    def _load_config(self, config_path: str) -> None:
        with open(config_path, 'r') as fd:
            try:
                self.config = yaml.safe_load(fd)
            except yaml.YAMLError as e:
                self.logger.error('Parse volume config %s FAILED', config_path)
                raise e

        self.logger.debug("volume config: %s", str(self.config))

        for k in ["apiVersion", "kind", "spec"]:
            if k not in self.config:
                raise KeyError(f"'{k}' is not defined in volumes config")

        if self.config["apiVersion"] != "longhorn-volume-manager/v1":
            self.logger.error("Invalid apiVersion defined in volume config")
            raise ValueError(f"apiVersion: {self.config['apiVersion']}' not supported")

        if self.config["kind"] != "LonghornVolumeSpec":
            self.logger.error("Invalid kind defined in volume config")
            raise ValueError(f"'kind: {self.config['kind']}' not supported")

        for k in ["volumes"]:
            if k not in self.config["spec"]:
                raise KeyError(f"'{k}' is not defined in volumes config")


    def generate_deployment_file(self, dest_name):
        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": self.deployment_name,
                "namespace": self.deployment_namespace
            },
            "spec": {
                "replicas": 1,
                "selector": {
                    "matchLabels": {
                        "app": self.deployment_name
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": self.deployment_name
                        }
                    },
                    "spec": {
                        "restartPolicy": "Always",
                        "containers": [{
                            "image": "traefik/traefikee-webapp-demo", # TODO change this later to our samba image
                            "imagePullPolicy": "IfNotPresent",
                            "name": self.deployment_name,
                            "volumeMounts": []
                        }],
                        "volumes": []
                    }
                }
            }
        }

        for k in self.config["spec"]["volumes"]:
            if any(x not in self.config["spec"]["volumes"][k] for x in ["createPVC", "namespace"]):
                continue

            if not self.config["spec"]["volumes"][k]["createPVC"]:
                continue

            if self.config["spec"]["volumes"][k]["namespace"] != self.deployment_namespace:
                self.logger.info("cross namespace not implemented, skip pvc %s", k)
                continue

            deployment["spec"]["template"]["spec"]["volumes"].append({
                "name": k,
                "persistentVolumeClaim": {
                    "claimName": k
                }
            })

            deployment["spec"]["template"]["spec"]["containers"][0]["volumeMounts"].append({
                "mountPath": "/samba/" + k,
                "name": k
            })

        with open(dest_name, 'w') as f:
            yaml.dump(deployment, f)
        os.system("cat {}".format(dest_name))


    def process(self):
        self._wait_start_delay()
        self.delete_deployment(self.deployment_namespace, self.deployment_name)
        with tempfile.NamedTemporaryFile(suffix='.yaml') as tmp:
            self.generate_deployment_file(tmp.name)
            self.create_deployment(self.deployment_namespace, tmp.name)
        time.sleep(1)


    def delete_deployment(self, namespace, name):
        # _ = self.apps_v1.delete_namespaced_deployment(
        #     name=name,
        #     namespace=namespace,
        #     body=client.V1DeleteOptions(
        #         propagation_policy="Foreground", grace_period_seconds=5
        #     ),
        # )

        os.system(f"kubectl delete deployment --namespace={namespace} {name}")
        self.logger.info("Deployment %s deleted.", name)


    def create_deployment(self, namespace, file_path):
        # with open(file_path) as f:
            # dep = yaml.safe_load(f)
            # _ = self.apps_v1.create_namespaced_deployment(
            #     body=dep, namespace=namespace)

        os.system(f"kubectl apply -f {file_path}")
        self.logger.info("Deployment created")



def setup_logging():
    logging.basicConfig(
        level=os.getenv('LOG_LEVEL', "INFO"),
        format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(stream=sys.stdout)
        ]
    )


if __name__ == "__main__":
    setup_logging()
    samba_server = SambaServerDeployment()
    samba_server.process()
