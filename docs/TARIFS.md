# Analyse des Tarifs et Modèle de Facturation

Ce document formalise les règles tarifaires, les paliers/tranches, les parts fixes, les taxes et les règles d'arrondi extraites des factures réelles fournies dans le dossier `facture/` pour les trois énergies : **Électricité**, **Gaz** et **Eau**.

---

## 1. Contexte Général et Localisation

- **Pays / Région** : Algérie, Wilaya d'Alger (Sidi Abdallah / Mahelma).
- **Fournisseur Électricité & Gaz** : **Sonelgaz Distribution** (Direction de distribution Sidi Abdallah).
- **Fournisseur Eau & Assainissement** : **SEAAL** (Société des Eaux et de l'Assainissement d'Alger).
- **Devise** : **Dinar algérien (DZD / DA)**.
- **Fréquence de facturation** : **Trimestrielle** (4 trimestres par an, cycle de ~90 à 92 jours).

---

## 2. Électricité (Sonelgaz — Tarif 54M Basse Tension Domestique)

### 2.1 Facture analysée
- **Facture n°** : 571260615440
- **Date d'émission** : 16/06/2026
- **Période** : 2ème Trimestre 2026 (environ 92 jours)
- **Prochaine relève** : 14/09/2026
- **Compteur n°** : 022150601804 | Puissance souscrite (PMD) : 6 kW | Coef multiplicateur : 1.0
- **Index précédent** : 6 639 kWh
- **Index nouveau** : 7 331 kWh
- **Consommation réelle facturée** : `7 331 - 6 639 = 692.00 kWh`

### 2.2 Paliers et tranches de consommation (Trimestre standard = 90 jours)
Le tarif réglementé 54M applique une tarification progressive par tranches :

| Tranche | Borne inférieure (kWh) | Borne supérieure (kWh) | Volume max tranche (kWh) | Prix unitaire HT (DA/kWh) | Taux TVA |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Tranche 1** | 0 | 125 | 125 | **1.7787** | 9 % |
| **Tranche 2** | 125 | 250 | 125 | **4.1789** | 9 % |
| **Tranche 3** | 250 | 1 000 | 750 | **4.8120** | 19 % |
| **Tranche 4** | > 1 000 | Illimité | - | **5.4800** | 19 % |

*Sur la facture de 692 kWh :*
- Tranche 1 (125 kWh) : `125 × 1.7787 = 222.3375 DA` → arrondi au centime : **222.34 DA**
- Tranche 2 (125 kWh) : `125 × 4.1789 = 522.3625 DA` → arrondi au centime : **522.36 DA**
- Sous-total Tranches 1+2 (HT à 9 %) : `222.34 + 522.36 = 744.70 DA`
- Tranche 3 (442 kWh) : `442 × 4.8120 = 2126.904 DA` → arrondi au centime : **2 126.90 DA** (HT à 19 %)
- **Total Électricité HT** : `744.70 + 2126.90 = 2 871.60 DA`

---

## 3. Gaz Naturel (Sonelgaz — Tarif 23M Basse Pression Domestique)

### 3.1 Facture analysée
- **Facture n°** : 571260615440 (facture conjointe électricité + gaz)
- **Compteur n°** : 230332101 | Débit max (DMD) : 5 m³/h
- **Index précédent** : 4 850 m³
- **Index nouveau** : 5 611 m³
- **Consommation volumique** : `5 611 - 4 850 = 761 m³`
- **Coefficient PCS** : **9.7 Th/m³** (Pouvoir Calorifique Supérieur)
- **Consommation énergétique facturée** : `761 m³ × 9.7 = 7 381.70 Th` (Thermies)

### 3.2 Paliers et tranches de consommation (Trimestre standard = 90 jours)
Le tarif 23M est progressif en thermies :

| Tranche | Borne inférieure (Th) | Borne supérieure (Th) | Volume max tranche (Th) | Prix unitaire HT (DA/Th) | Taux TVA |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Tranche 1** | 0 | 1 125 | 1 125 | **0.1682** | 9 % |
| **Tranche 2** | 1 125 | 2 500 | 1 375 | **0.3245** | 9 % |
| **Tranche 3** | 2 500 | 7 500 | 5 000 | **0.4025** | 19 % |
| **Tranche 4** | > 7 500 | Illimité | - | **0.4599** | 19 % |

*Sur la facture de 7 381.70 Th :*
- Tranche 1 (1 125 Th) : `1 125 × 0.1682 = 189.225 DA` → arrondi au centime : **189.23 DA**
- Tranche 2 (1 375 Th) : `1 375 × 0.3245 = 446.1875 DA` → arrondi au centime : **446.19 DA**
- Sous-total Tranches 1+2 (HT à 9 %) : `189.23 + 446.19 = 635.42 DA`
- Tranche 3 (4 881.70 Th) : `4 881.70 × 0.4025 = 1964.88425 DA` → arrondi au centime : **1 964.88 DA** (HT à 19 %)
- **Total Gaz HT** : `635.42 + 1 964.88 = 2 600.30 DA`

---

## 4. Parts Fixes et Taxes Sonelgaz (Électricité + Gaz)

### 4.1 Redevances fixes (Abonnement)
- **Montant trimestriel HT** : **164.16 DA**
- **Taux TVA applicable** : **9 %**
- Répartition par défaut : Électricité (puissance 6 kW) ~ 78.66 DA / Gaz (5 m³/h) ~ 85.50 DA (28.50 DA/mois).

### 4.2 Calcul global HT Sonelgaz
- Électricité HT : **2 871.60 DA**
- Gaz HT : **2 600.30 DA**
- Redevance fixe HT : **164.16 DA**
- **Total Montant HT** : `2 871.60 + 2 600.30 + 164.16 =` **5 636.06 DA**

### 4.3 Taxes et TVA Sonelgaz
1. **Assiette TVA 9 %** : `744.70 (Élec T1+T2) + 635.42 (Gaz T1+T2) + 164.16 (Redevance fixe) = 1 544.28 DA`
   - `TVA 9 % = 1 544.28 × 0.09 = 138.9852 DA` → arrondi au centime : **138.99 DA**
2. **Assiette TVA 19 %** : `2 126.90 (Élec T3) + 1 964.88 (Gaz T3) = 4 091.78 DA`
   - `TVA 19 % = 4 091.78 × 0.19 = 777.4382 DA` → arrondi au centime : **777.44 DA**
3. **Total TVA** : `138.99 + 777.44 =` **916.43 DA**
4. **Droit Fixe sur consommation** (taxe réglementaire directe) : **200.00 DA** (100 DA élec + 100 DA gaz)
5. **Taxe d'habitation** (taxe communale) : **200.00 DA**
6. **Net à payer TTC** : `5 636.06 (HT) + 916.43 (TVA) + 200.00 + 200.00 =` **6 952.49 DA**
7. **Timbre fiscal (optionnel en espèces)** : **70.00 DA** → Total espèces : **7 022.49 DA**

---

## 5. Eau & Assainissement (SEAAL — Tarif Résidentiel / Domestique)

### 5.1 Facture analysée
- **Facture n°** : F055154807
- **Date d'émission** : 13/04/2025
- **Période** : 13/01/2025 au 09/04/2025 (2° QUARTER / 2025 — 86 jours réels / 90 jours contractuels)
- **Compteur n°** : 122PA027035
- **Index précédent** : 103 m³
- **Index nouveau** : 120 m³
- **Consommation facturée** : `120 - 103 = 17 m³`

### 5.2 Structure tarifaire binôme SEAAL (Eau Potable + Assainissement)

#### A. Alimentation en Eau Potable (AEP)
- **Part fixe (Fixed Fees & Charges)** : **240.00 DA HT** par trimestre
- **Tranches volumiques d'eau** (grille nationale décret 05-13 pour Alger) :
  - **Tranche 1 (0 à 25 m³)** : **6.30 DA/m³ HT**
  - **Tranche 2 (26 à 55 m³)** : **20.48 DA/m³ HT**
  - **Tranche 3 (56 à 82 m³)** : **34.65 DA/m³ HT**
  - **Tranche 4 (> 82 m³)** : **40.95 DA/m³ HT**

*Sur la facture de 17 m³ :*
- Consommation Tranche 1 : `17 × 6.30 = 107.10 DA HT`
- **Sous-total Eau HT** : `240.00 + 107.10 = 347.10 DA HT`

#### B. Assainissement Collectif
- **Part fixe (Fixed Fees & Charges)** : **60.00 DA HT** par trimestre
- **Tranches volumiques d'assainissement** :
  - **Tranche 1 (0 à 25 m³)** : **2.35 DA/m³ HT**
  - **Tranche 2 (26 à 55 m³)** : **7.64 DA/m³ HT**
  - **Tranche 3 (56 à 82 m³)** : **12.93 DA/m³ HT**
  - **Tranche 4 (> 82 m³)** : **15.28 DA/m³ HT**

*Sur la facture de 17 m³ :*
- Consommation Tranche 1 : `17 × 2.35 = 39.95 DA HT`
- **Sous-total Assainissement HT** : `60.00 + 39.95 = 99.95 DA HT`

#### C. Total Hors Taxes SEAAL
- `Total HT = 347.10 + 99.95 =` **447.05 DA HT**

### 5.3 Taxes, Redevances et Totaux SEAAL
1. **TVA à 9 %** :
   - TVA Eau : `347.10 × 0.09 = 31.239 DA` → **31.24 DA**
   - TVA Assainissement : `99.95 × 0.09 = 8.9955 DA` → **9.00 DA**
   - Total TVA : `31.24 + 9.00 =` **40.24 DA** (assiette 447.05 DA)
2. **M.F (إتاوة التسيير - Redevance d'assainissement / gestion)** :
   - Assiette : volume consommé (`17 m³`)
   - Taux : **3.00 DA/m³**
   - Montant : `17 × 3.00 =` **51.00 DA**
3. **W.Q.F (إتاوة نوعية الماء - Redevance qualité de l'eau)** :
   - Assiette : montant consommation eau potable (`107.10 DA`)
   - Taux : **4 %**
   - Montant : `107.10 × 0.04 = 4.284 DA` → **4.28 DA**
4. **W.S.F (إتاوة إقتصاد الماء - Redevance économie d'eau)** :
   - Assiette : montant consommation eau potable (`107.10 DA`)
   - Taux : **4 %**
   - Montant : `107.10 × 0.04 = 4.284 DA` → **4.28 DA**
5. **Total des taxes et redevances** :
   - `40.24 (TVA) + 51.00 (M.F) + 4.28 (W.Q.F) + 4.28 (W.S.F) =` **99.80 DA**
6. **Total TTC (Total after tax)** :
   - `447.05 (HT) + 99.80 (Taxes) =` **546.85 DA**
7. **Droit de timbre (Duty Stamp - espèces)** : **6.00 DA** → **Total dû : 552.85 DA**

---

## 6. Synthèse de Rétro-validation

Les deux factures fournies ont été entièrement recalculées avec les règles exactes :

| Facture | Énergie | Montant réel facture | Montant calculé par le modèle | Écart absolu | Écart relatif |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Sonelgaz T2 2026** | Électricité + Gaz | **6 952.49 DA** (TTC hors timbre)<br>**7 022.49 DA** (avec timbre) | **6 952.49 DA**<br>**7 022.49 DA** | **0.00 DA** | **0.000 %** |
| **SEAAL T2 2025** | Eau | **546.85 DA** (TTC hors timbre)<br>**552.85 DA** (avec timbre) | **546.85 DA**<br>**552.85 DA** | **0.00 DA** | **0.000 %** |

**Précision atteinte : 100.000 % (écart nul au centime près).**
