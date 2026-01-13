# 🚀 Procédure de migration vers la séparation Dev/Prod

## ⚠️ IMPORTANT : Suivre cet ordre exactement

### Étape 1 : Créer la branche `main` AVANT de merger

```bash
# Depuis ton local, sur Dockerized à jour
git checkout Dockerized
git pull origin Dockerized

# Créer main à partir de Dockerized (état actuel de prod)
git checkout -b main
git push origin main
```

### Étape 2 : Configurer les protections sur GitHub

1. Aller sur GitHub → Settings → Branches
2. Ajouter une règle pour `main` :
   - ✅ Require pull request before merging
   - ✅ Require status checks to pass
   - ✅ Do not allow bypassing the above settings

### Étape 3 : Vérifier que le workflow de production existe sur `main`

Le workflow `deploy-production.yaml` doit être sur `main` AVANT de modifier `Dockerized`.

**Option A (recommandée) :** Cherry-pick le workflow sur main
```bash
git checkout main
git cherry-pick <commit-hash-du-deploy-production.yaml>
git push origin main
```

**Option B :** Merger d'abord la PR vers Dockerized, puis immédiatement vers main
```bash
# Après merge de la PR vers Dockerized
git checkout Dockerized
git pull origin Dockerized
git checkout main
git merge Dockerized
git push origin main
```

### Étape 4 : Merger la PR vers Dockerized

Maintenant tu peux merger ta PR `feature/split-settings-env-separation` → `Dockerized`

### Étape 5 : Synchroniser main avec Dockerized

```bash
git checkout main
git merge Dockerized
git push origin main
```

---

## 🔄 Nouveau workflow de déploiement

Après cette migration :

| Action | Résultat |
|--------|----------|
| Push vers `Dockerized` | ✅ Build staging image, ❌ Pas de déploiement |
| Push vers `main` | ✅ Tests + Build + Déploiement prod |
| PR vers `main` | ✅ Tests uniquement |

---

## 🆘 Rollback si problème

Si tu dois déployer en urgence et que quelque chose ne marche pas :

```bash
# Déclencher manuellement le déploiement
# GitHub → Actions → Deploy to Production → Run workflow
# Taper "deploy" pour confirmer
```

Ou restaurer l'ancien build.yaml :
```bash
git checkout main
git revert <commit-qui-a-modifié-build.yaml>
git push origin main
```

