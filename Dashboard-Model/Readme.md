Good. Now we simplify everything so this never confuses you again.

You now have only **one environment: `.venv`**. That’s perfect.

From now on, every single time you close the tab and reopen it, you only need to do **three things**.

---

# ✅ Every Time You Reopen the Project

### Step 1 — Go to your project folder

```powershell
cd D:\EXPO\Motor
```

---

### Step 2 — Activate your virtual environment

```powershell
.\.venv\Scripts\Activate
```

If it works, you will see:

```
(.venv) PS D:\EXPO\Motor>
```

That means you're inside the correct environment.

---

### Step 3 — Run the dashboard

```powershell
python -m streamlit run app.py
```

Your browser will open at:

```
http://localhost:8501
```

That’s it.

---

# ❗ Important Rules (So You Never Break It Again)

### 1️⃣ Never use:

```
streamlit run app.py
```

Always use:

```
python -m streamlit run app.py
```

This guarantees it uses the correct environment.

---

### 2️⃣ Never reinstall requirements unless:

* You deleted `.venv`
* You changed Python version
* You changed `requirements.txt`

You do NOT need to install packages every time.

---

### 3️⃣ If activation ever fails

If you get execution policy error:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate again.

---

# 💡 Mental Model (So You Understand It Forever)

Closing the tab:

* Does NOT delete `.venv`
* Does NOT uninstall packages
* It only deactivates the environment

Reopening = just reactivate it.

Think of `.venv` like turning on your lab equipment.
Closing the tab is just switching it off.
You don’t rebuild the lab every time.

---

# 🚀 Ultra Short Version (Memorize This)

Every time:

```
cd D:\EXPO\Motor
.\.venv\Scripts\Activate
python -m streamlit run app.py


cd D:\EXPO\Motor
.\.venv\Scripts\Activate
python -m streamlit run app_new.py
```

That’s your permanent workflow.

---

If you want, I can also show you how to make it one-click with a `.bat` file so you never type these commands again.
