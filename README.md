# Conso Maison ⚡🔥💧

Application web auto-hébergée sous Docker, installable en **PWA sur iPhone**, conçue pour suivre la consommation manuelle d'**électricité, de gaz et d'eau** et estimer avec précision les factures trimestrielles.

L'application intègre le modèle de tarification officiel algérien (**Sonelgaz** pour l'électricité et le gaz, **SEAAL** pour l'eau et l'assainissement), rétro-validé au centime près sur factures réelles.

---

## 📱 Points forts et Fonctionnalités

- **Saisie du vendredi en 15 secondes** : Feuille modale plein écran dédiée avec aperçu instantané du coût et du delta en direct pendant la frappe.
- **Facturation Sonelgaz conjointe** : Électricité + Gaz regroupés sur une facture unique avec mutualisation des frais fixes, taxes et décomposition par tranches (TVA 9 % et 19 %).
- **Facturation SEAAL** : Décomposition binôme Eau potable + Assainissement, TVA 9 % et redevances réglementaires (M.F, W.Q.F, W.S.F).
- **Projections trimestrielles** : Scénarios bas / central / haut basés sur les 4 dernières semaines pondérées, jauge de palier et indice de confiance.
- **Analyses temporelles** : Vues par semaine ISO (avec moyenne mobile 4 semaines), mois, trimestre, année, et suivi du taux journalier moyen.
- **Design System iOS "Nuit"** : Dark-first, respect des safe areas iPhone, chiffres tabulaires, zone tactile minimale de 44 px, barre d'onglets flottante avec effet verre dépoli.
- **Mode hors-ligne PWA** : Coquille et données en cache via Service Worker Workbox.

---

## 🛠️ Stack Technique

- **Backend** : Python 3.12, FastAPI, SQLAlchemy 2 (mode SQLite WAL), Pydantic v2, Alembic.
- **Frontend** : React 18, Vite, TypeScript, Tailwind CSS, TanStack React Query, React Router, Recharts, Lucide Icons.
- **PWA** : `vite-plugin-pwa` (Workbox, manifest, icônes tactiles iOS).
- **Conteneurisation** : Dockerfile multi-stage (build Node 22 + runner Python slim), `docker-compose.yml`.

---

## 🚀 Démarrage Rapide

### 1. Configuration
Créez un fichier `.env` à la racine (ou copiez `.env.example`) :

```bash
cp .env.example .env
```

Renseignez votre mot de passe d'accès unique :
```env
APP_PASSWORD=mon_mot_de_passe_secret
SECRET_KEY=cle_secrete_aleatoire_unique_a_generer
TZ=Africa/Algiers
```

### 2. Lancement avec Docker Compose

```bash
docker compose up -d --build
```

L'application est immédiatement accessible sur `http://localhost:8080`.

---

## 🔒 HTTPS & Installation PWA sur iPhone

Pour pouvoir installer l'application en PWA sur iPhone (**Safari → Icône Partager → Sur l'écran d'accueil**), **Apple impose une connexion HTTPS**.

Voici les 2 méthodes recommandées :

### Option A : Via Tailscale (Recommandé, simple et sécurisé)
Si vous utilisez Tailscale sur votre serveur/NAS et votre iPhone :

```bash
# Expose l'application en HTTPS avec un certificat Let's Encrypt automatique
tailscale serve --bg https / http://127.0.0.1:8080
```
Ouvrez l'URL fournie par Tailscale dans Safari sur votre iPhone et appuyez sur **Sur l'écran d'accueil**.

### Option B : Profil Caddy inclus
Si vous disposez d'un nom de domaine ou souhaitez un certificat local :

```bash
DOMAIN=conso.mondomaine.com docker compose --profile with-caddy up -d
```

---

## 💾 Sauvegarde à chaud de la base de données

La base SQLite est stockée dans le volume Docker nommé `data` (monté sur `/data/conso_maison.db`). Grâce au mode **WAL** (Write-Ahead Logging), vous pouvez copier la base à chaud sans arrêter le conteneur :

```bash
# Sauvegarde instantanée
docker compose exec app sqlite3 /data/conso_maison.db ".backup '/data/backup_$(date +%Y%m%d_%H%M%S).db'"

# Exporter le fichier sur la machine hôte
docker cp conso-maison-app:/data/conso_maison.db ./sauvegarde_conso.db
```

Vous pouvez également faire un export JSON complet directement depuis l'onglet **Réglages** de l'application.

---

## 🧪 Tests

### Tests Backend (Python / pytest)
```bash
python -m pytest backend/tests/
```
*Vérifie la rétro-validation des factures au centime près (0.00 % d'écart), la répartition linéaire journalière et l'API.*

### Tests Frontend (Vitest)
```bash
cd frontend
npm test
```
*Vérifie les fonctions de formatage et calculs côté client.*

---

## 📄 Licence
Usage personnel privé.
