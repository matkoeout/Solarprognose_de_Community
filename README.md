# Solarprognose.de (Community Integration for Home Assistant)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

[🇩🇪 Deutsch](#-deutsch) | [🇺🇸 English](#-english)

---

<a name="-deutsch"></a>
## 🇩🇪 Deutsch

### WICHTIGER HINWEIS / HAFTUNGSAUSSCHLUSS

DIESE SOFTWARE WIRD **OHNE JEGLICHE GARANTIE** ZUR VERFÜGUNG GESTELLT.

DIE NUTZUNG ERFOLGT **AUSSCHLIESSLICH AUF EIGENE GEFAHR**.

DER AUTOR ÜBERNIMMT **KEINERLEI HAFTUNG** FÜR:
- FALSCHE, UNVOLLSTÄNDIGE ODER VERALTETE PROGNOSEDATEN
- FINANZIELLE VERLUSTE, ENTGANGENE ERTRÄGE ODER FEHLENTSCHEIDUNGEN
- FEHLFUNKTIONEN, AUSFÄLLE ODER DATENVERLUSTE
- SCHÄDEN AN HARDWARE, SOFTWARE ODER PV-ANLAGEN
- FOLGESCHÄDEN JEGLICHER ART

INSBESONDERE SIND DIE BERECHNETEN PROGNOSEWERTE **NICHT** FÜR:
- ABRECHNUNGEN
- GARANTIE- ODER GEWÄHRLEISTUNGSZWECKE
- VERTRAGLICHE ODER RECHTLICHE ENTSCHEIDUNGEN
- KRITISCHE STEUERUNGEN
GEEIGNET.

MIT DER INSTALLATION UND NUTZUNG DIESER INTEGRATION ERKLÄRST DU DICH AUSDRÜCKLICH DAMIT EINVERSTANDEN.

---

### Beschreibung
Diese Custom Integration für Home Assistant bindet die WebAPI von Solarprognose.de ein und stellt PV-Ertragsprognosen als Sensoren zur Verfügung. Es handelt sich um eine **nicht-offizielle Community-Integration**. Es besteht **keine Verbindung** zum Betreiber von Solarprognose.de.

### 🔑 API-Zugang erhalten (Kurzanleitung)
Um diese Integration zu nutzen, benötigst du einen Account bei Solarprognose.de:
1. Registriere dich auf [Solarprognose.de](https://www.solarprognose.de).
2. Erstelle unter **"Anlageneinstellungen"** eine neue PV-Anlage.
3. Gehe zu **"User-Einstellungen"** -> **"Schnittstelle / API"**.
4. Kopiere deinen **API-Key** oder die fertige **API-URL**.

### Installation via HACS (Empfohlen)
[![Open your Home Assistant instance and open a repository window in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=matkoeout&repository=link_solarprognose_de&category=Integration)

1. Klicke auf den Button oben (erfordert [My Home Assistant](https://my.home-assistant.io/)).
2. Manuell: **HACS** -> **Integrationen** -> Drei Punkte (oben rechts) -> **Benutzerdefinierte Repositories**.
3. URL: `https://github.com/matkoeout/link_solarprognose_de` | Kategorie: **Integration**.
4. Klicke auf **Herunterladen** und starte Home Assistant neu.

---

<a name="-english"></a>
## 🇺🇸 English

### IMPORTANT NOTICE / DISCLAIMER

THIS SOFTWARE IS PROVIDED **WITHOUT ANY WARRANTY**.

USE AT **YOUR OWN RISK**.

THE AUTHOR ASSUMES **NO LIABILITY** FOR:
- INCORRECT, INCOMPLETE OR OUTDATED FORECAST DATA
- FINANCIAL LOSSES, LOST PROFITS OR WRONG DECISIONS
- MALFUNCTIONS, FAILURES OR DATA LOSS
- DAMAGE TO HARDWARE, SOFTWARE OR PV SYSTEMS
- CONSEQUENTIAL DAMAGES OF ANY KIND

IN PARTICULAR, THE CALCULATED FORECAST VALUES ARE **NOT** SUITABLE FOR:
- BILLING PURPOSES
- WARRANTY OR GUARANTEE PURPOSES
- CONTRACTUAL OR LEGAL DECISIONS
- CRITICAL CONTROLS

BY INSTALLING AND USING THIS INTEGRATION, YOU EXPRESSLY AGREE TO THESE TERMS.

---

### Description
This custom integration connects the Solarprognose.de WebAPI to Home Assistant. This is an **unofficial community integration** and has no affiliation with the operators of Solarprognose.de.

### 🔑 How to get API Access
1. Register at [Solarprognose.de](https://www.solarprognose.de).
2. Go to **"System Settings"** (Anlageneinstellungen) and create your PV system.
3. Navigate to **"User Settings"** -> **"API / Interface"**.
4. Copy your **API Key** or the full **API URL**.

### Installation via HACS (Recommended)
[![Open your Home Assistant instance and open a repository window in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=matkoeout&repository=link_solarprognose_de&category=Integration)

1. Click the button above.
2. Manual: Open **HACS** -> **Integrations** -> Three dots -> **Custom repositories**.
3. URL: `https://github.com/matkoeout/link_solarprognose_de` | Category: **Integration**.
4. Click **Download** and restart Home Assistant.

### Sensors
* **Energy:** Today Total, Tomorrow Total, Remaining Day, Forecast (kWh)
* **Power:** Current Hour, Next Hour (W)
* **Status:** API Status, API Requests Today, Last/Next Update

### License
MIT License.