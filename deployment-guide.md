1. Test Django
```
python manage.py test
```
2. Build Container
```
docker build --platform linux/amd64 -f Dockerfile \
    -t registry.digitalocean.com/otace/gestionhydro-amd64:latest \
    -t registry.digitalocean.com/otace/gestionhydro-amd64:v1 \
    .
```
3. Push Image to Registry (DO)
```
docker push registry.digitalocean.com/otace/gestionhydro-amd64 --all-tags
```
4. Update Secrets
```
kubectl delete secret django-deploy-env
kubectl create secret generic django-deploy-env --from-env-file=k8s/config/prod.env
```

[//]: # (5. Deploying Services &#40;Persistant Storage Volume&#41;)

[//]: # (```)

[//]: # (kubectl apply -f k8s/deployment/volumes.yaml)

[//]: # (```)

5. Update ConfigMap for Nginx
```
kubectl delete configmap nginx-configmap
kubectl create configmap nginx-configmap --from-file=k8s/config/nginx.conf
```
6. Update Deployment NGINX Proxy
```
kubectl apply -f k8s/deployment/nginx.yaml 
```
7. Update Deployment of Services Load Balancer and Django Node port
```
kubectl apply -f k8s/deployment/services.yaml
```
8. Update Deployment of Django + Celery + Deploying Static Files
```
kubectl apply -f k8s/deployment/django-deployment.yaml
```
9. Wait for Rollout to Finish
```
kubectl rollout status deployment/gestionhydro-deployment 
```

10. Migrate the database
```
export SINGLE_POD_NAME=$(kubectl get pod -l app=gestionhydro-deployment -o jsonpath="{.items[0].metadata.name}")
```
Run the migrations Migration
```
kubectl exec -it $SINGLE_POD_NAME -- bash /app/scripts/migration.sh 
```

[//]: # (10. Ingress Controller)

[//]: # (```)

[//]: # (kubectl create ingress demo --class=nginx --rule [DNS_NAME]/=demo:80)

[//]: # (```)
