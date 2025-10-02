## 🔹 Creazione di un ambiente virtuale

Per ciascun pacchetto o modulo che vuoi eseguire, segui questi passaggi:

### 1. Crea un ambiente virtuale
```bash
python3 -m venv venv
````

### 2. Attiva l’ambiente

Su **macOS/Linux**:

```bash
source venv/bin/activate
```

Su **Windows (PowerShell)**:

```powershell
venv\Scripts\activate
```

### 3. Installa le dipendenze

Una volta attivato l’ambiente, installa le dipendenze dal file `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## 🔹 Disattivare l’ambiente

Quando hai finito di lavorare, puoi disattivare l’ambiente con:

```bash
deactivate
```

---

## 🔹 File requirements.txt

Il progetto include un file `requirements.txt` con tutte le dipendenze necessarie:

```txt
bosdyn-api==5.0.1
bosdyn-client==5.0.1
bosdyn-core==5.0.1
bosdyn-mission==5.0.1
bosdyn-choreography-client==5.0.1
bosdyn-choreography-protos==5.0.1
bosdyn-orbit==5.0.1
```

---

## 🔹 Consigli

* Usa un ambiente virtuale **per ogni pacchetto o progetto**, così da mantenere le dipendenze separate.
* Se aggiorni i pacchetti, puoi rigenerare il file `requirements.txt` con:

  ```bash
  pip freeze > requirements.txt
  ```

---

## 🔹 Riferimenti

* [Python venv documentation](https://docs.python.org/3/library/venv.html)
* [Boston Dynamics Spot SDK](https://dev.bostondynamics.com/)
