# Pollini & Sintomi

Programma per Windows per tenere un diario giornaliero delle allergie: ogni
giorno segni quanti pollini ci sono nell'aria e che sintomi hai avuto. Dopo un
po' che raccogli dati, il programma li incrocia e ti dice quali pollini sembrano
darti più fastidio, così puoi farti un'idea delle cause.

L'interfaccia usa toni di verde, giallo e bianco (stile solarpunk) ed è pensata
per inserire i dati in fretta, con pochi click.

## Scaricare

- **Programma già pronto (.exe)**: vai nella pagina
  [Releases](https://github.com/Xaynet/pollen-symptoms-calculator/releases) e
  scarica `PolliniSintomi.exe` dall'ultima versione. Si avvia con un doppio
  click, non serve installare Python.
- **Codice sorgente**: dal bottone verde **Code** in alto scegli
  *Download ZIP*, oppure prendi lo zip dalla stessa pagina delle Releases.

L'`.exe` delle Releases viene compilato in automatico da una GitHub Action ogni
volta che si pubblica una nuova versione (vedi più sotto). Se preferisci puoi
sempre crearlo da te seguendo le istruzioni in fondo.

## Cosa fa

- Calendario del mese in cui si vede a colpo d'occhio quali giorni hai già
  compilato. I giorni compilati sono colorati a seconda di quanto sono stati
  pesanti i sintomi (dal verde chiaro all'arancione); quelli ancora da fare
  restano bianchi.
- Pagina del singolo giorno con tutti i 25 pollini e i 12 sintomi su una sola
  schermata. Per ogni voce scegli il livello con un click (per i pollini:
  Assente / Basso / Medio / Alto; per i sintomi sei livelli). Niente finestre
  che si aprono e chiudono. Il valore selezionato si colora in base
  all'intensità (dal verde all'arancione), per vedere a colpo d'occhio la
  gravità.
- Un interruttore (impostazione unica, valida per tutti i giorni) per mostrare
  tutti i pollini oppure solo i cinque coperti da Open-Meteo, quando vuoi
  inserire i dati ancora più in fretta.
- Bottone "Oggi" che porta dritto alla giornata di oggi, per la registrazione
  di tutti i giorni.
- Una pagina di analisi che calcola la correlazione tra il livello di ogni
  polline e quanto sono stati forti i sintomi, mette in classifica i pollini
  più sospetti e indica i sintomi che pesano di più.
- Pulsante per **precompilare alcuni pollini** scaricandoli dalle previsioni
  gratuite di Open-Meteo, così non li devi cercare a mano (vedi sotto).
- I dati restano in un file sul disco (SQLite) che puoi copiare per fare un
  backup e portare su un altro PC.

## Com'è fatto

Python (3.10 o successivo), interfaccia con
[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) e dati su
SQLite (il modulo `sqlite3` è già incluso in Python). L'unica libreria da
installare è CustomTkinter. Per l'eseguibile si usa PyInstaller.

## Avviare il programma

Serve Python 3.10 o successivo
([download](https://www.python.org/downloads/); durante l'installazione spunta
"Add Python to PATH").

Il modo più rapido è fare doppio click su `avvia.bat`: la prima volta si
prepara l'ambiente e scarica quel che serve, le volte dopo apre direttamente il
programma.

Se preferisci la riga di comando:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## Creare l'eseguibile (.exe)

Doppio click su `crea_exe.bat`. Quando finisce trovi il file in
`dist\PolliniSintomi.exe`: è autonomo, puoi copiarlo dove vuoi e farlo partire
anche su un PC senza Python.

A mano invece:

```powershell
pip install pyinstaller
pyinstaller --noconfirm --windowed --onefile ^
    --name "PolliniSintomi" ^
    --collect-all customtkinter ^
    main.py
```

Il `--collect-all customtkinter` serve perché CustomTkinter porta con sé dei
file di tema che altrimenti PyInstaller si dimentica di includere.

## Pubblicare una nuova versione su GitHub

C'è una GitHub Action (`.github/workflows/build-release.yml`) che compila
l'`.exe` su una macchina Windows e lo allega alla release. Per farla partire
basta creare un tag che inizia per `v` e pubblicarlo:

```powershell
git tag v1.0.0
git push origin v1.0.0
```

Dopo qualche minuto, nella pagina Releases comparirà la nuova versione con
`PolliniSintomi.exe` pronto da scaricare. In alternativa si può lanciare la
compilazione a mano dalla scheda **Actions** del repo (pulsante *Run workflow*):
in quel caso l'`.exe` si scarica dagli *Artifacts* della run.

## Precompilare i pollini da Open-Meteo

Nella schermata del giorno c'è il pulsante **"🌍 Precompila da Open-Meteo"**.
La prima volta ti chiede la città (la salva, così non te la richiede più; puoi
cambiarla quando vuoi col pulsante **"📍 Città"**), poi scarica le previsioni
pollini per quel giorno e imposta da solo i livelli.

Va detto chiaramente cosa copre: le fonti automatiche gratuite danno solo
**cinque** dei pollini della lista — **betulla, graminacee, assenzio, olivo e
ambrosia**. Tutti gli altri restano da inserire a mano, perché nessun servizio
gratuito li fornisce per le singole specie. I valori (granuli/m³, media del
giorno) vengono convertiti in Assente/Basso/Medio/Alto con soglie indicative per
famiglia, che puoi ritoccare in `pollen_app/openmeteo.py` se vuoi.

Serve la connessione a Internet solo nel momento in cui premi il pulsante; per
il resto l'app funziona offline. Non richiede chiavi o registrazioni e usa solo
moduli standard di Python.

Nella stessa schermata c'è l'interruttore **"Mostra solo i pollini di
Open-Meteo"**: è un'impostazione globale (vale per tutti i giorni, non solo per
quello aperto) e serve a inserire i dati più in fretta vedendo solo le cinque
piante che si possono anche precompilare. Importante: con il filtro attivo, i
pollini nascosti **non** vengono registrati come "Assente", ma restano
semplicemente *non valutati* per quel giorno (nessun dato scritto), e in quanto
tali **non influenzano le statistiche** — l'analisi considera solo i giorni in
cui una pianta è stata effettivamente valutata.

## Dove finiscono i dati

Tutto sta in un unico file:

```
C:\Users\<utente>\Documents\PollenSymptomsCalculator\pollen_data.db
```

Per il backup basta copiare quel file. Se vuoi tenerlo da un'altra parte (o
provare il programma su una copia separata) puoi indicare un percorso diverso
con la variabile d'ambiente `POLLEN_DB_PATH`:

```powershell
$env:POLLEN_DB_PATH = "D:\backup\pollen_data.db"
python main.py
```

Il percorso che sta usando in quel momento è scritto in basso nella finestra,
accanto ai pulsanti di backup.

### Backup e ripristino dall'app

In fondo alla finestra ci sono due pulsanti:

- **💾 Esporta backup** salva una copia completa dei dati in un file `.db` a
  tua scelta (utile prima di un aggiornamento, o per portarli su un altro PC).
- **↩ Ripristina backup** sostituisce i dati attuali con quelli di un file di
  backup. Chiede conferma prima di procedere e rifiuta i file che non sono
  backup validi.

### Aggiornare l'app senza perdere i dati

I dati non stanno dentro l'eseguibile ma nel file qui sopra, quindi per passare
a una versione nuova basta sostituire `PolliniSintomi.exe` (o aggiornare il
sorgente): la nuova versione riapre lo stesso file e ritrovi tutto. Se una
versione futura cambia la struttura del database, l'app la aggiorna da sola al
primo avvio (migrazioni basate su `PRAGMA user_version`) senza toccare i dati
già inseriti. Per sicurezza, prima di un aggiornamento importante puoi sempre
fare un'esportazione di backup.

## I file del progetto

```
pollen-symptoms-calculator/
├── avvia.bat                # doppio click: avvia il programma
├── crea_exe.bat             # doppio click: crea l'eseguibile
├── main.py                  # avvio
├── requirements.txt
├── README.md
├── .gitignore
├── .github/workflows/
│   └── build-release.yml    # compila e pubblica l'exe su GitHub
└── pollen_app/
    ├── __init__.py
    ├── constants.py         # elenco piante, sintomi e livelli
    ├── theme.py             # colori e font
    ├── dates_it.py          # nomi di mesi e giorni in italiano
    ├── db.py                # lettura/scrittura su SQLite
    ├── openmeteo.py         # scarico pollini da Open-Meteo
    ├── analysis.py          # calcolo correlazioni e suggerimenti
    └── ui/
        ├── calendar_view.py # il calendario
        ├── day_editor.py    # la pagina del singolo giorno
        └── analysis_view.py # la pagina dell'analisi
```

## Piante e sintomi gestiti

Piante: aceracee, betulla, chenopodiacee/amarantacee, assenzio, ambrosia,
nocciolo, carpino, carpino nero, cupressacee/taxacee, castagno, faggio, quercia,
graminacee, olivo, orno, ligustro, frassino, frassino comune, pinacee,
platanacee, poligonacee, pioppo, salice, ulmacee, urticacee.

Livelli di polline: Assente, Basso, Medio, Alto.

Sintomi: tosse, gonfiore occhi, gonfiore labbra, prurito bocca, prurito naso,
starnuti, gonfiore mani, muco, stanchezza, mal di testa, difficoltà
respiratoria, sibilo.

Livelli dei sintomi: Assente, Molto lieve, Tollerabile, Fastidioso,
Problematico, Eccessivo.

## Una precisazione

L'analisi si basa solo sui dati che inserisci e segnala delle coincidenze: il
fatto che un polline e dei sintomi vadano spesso insieme non vuol dire per forza
che sia la causa. Prendila come un punto di partenza da discutere con il medico
o l'allergologo.
