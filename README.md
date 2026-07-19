<div align="center">
  <img src="https://media.giphy.com/media/26xBEH81H0B4yV4fC/giphy.gif" alt="JARVIS Core" width="150"/>
  <h1>⚡ A.E.R.O. - The Agentic Execution & Responsive Oracle ⚡</h1>
  <p><strong>Your Ultimate Personal Local AI Assistant</strong></p>
  <p><i>Command Your OS. Talk in Real-Time. Fully Private. Breathtaking 3D UI.</i></p>
</div>

---

## 🌌 What is A.E.R.O.?

AERO is not just another chatbot. It is a **fully agentic**, high-performance AI assistant that runs 100% locally on your machine. Featuring a stunning **WebGL 3D Neural Network Hologram**, AERO listens to you, speaks to you in real-time, and—most importantly—**controls your PC**. 

Want to open an app? Create a file? Kill a task? Just ask AERO. 

It operates seamlessly as your digital co-pilot with zero data leaving your machine! 🚀

---

## 🔥 CRAZY Features

- 🧠 **Full Agentic OS Control**: AERO generates and executes PowerShell commands in the background securely. Tell AERO to "open Notepad" or "write a Python script on my desktop," and watch it happen instantly.
- 🔮 **Volumetric 3D Hologram GUI**: A beautiful, interactive, glowing particle system built with Three.js. It breathes, reacts, and dynamically shifts when AERO is "thinking." You can even pan and zoom into the neural network using your mouse!
- 🎙️ **Real-Time Voice & Text Streaming**: Zero latency. AERO speaks sentences back to you **as they stream** from the local LLM. No waiting for the whole paragraph to finish before it starts talking!
- 🕵️ **100% Private & Secure**: Backed by [Ollama](https://ollama.com/), the brain runs locally. No API keys, no subscriptions, no data harvesting.
- 🤵 **The "BOSS" Protocol**: AERO is designed with a calm, composed, slightly witty J.A.R.V.I.S.-like persona that always treats you as the BOSS.
- 🌐 **Deployable to the Web**: You can host the beautiful 3D UI on GitHub Pages for free! It will securely connect to the visitor's local Ollama instance over their local loopback.

---

## 🛠️ Getting Started (Local Boss Mode)

To unlock the **Agentic OS Control**, you need to run the Python backend on your machine. This acts as the bridge between the beautiful UI and your operating system.

### Prerequisites:
1. **Windows OS** (powershell required for Agentic commands)
2. **Python 3.10+**
3. **[Ollama](https://ollama.com/)** installed and running on your machine.
   *Pull the default model:*
   ```bash
   ollama pull llama3
   ```

### 🚀 One-Click Launch:
1. Double-click `run_aero.bat` in the project folder.
2. Boom. A browser window opens at `http://localhost:8000`.
3. Give AERO a command like: *"Boss needs a new text file created on my desktop."*

---

## 🌍 GitHub Pages Deployment (Web Client Mode)

Want to show off the insane UI to the world? You can deploy the `index.html` to **GitHub Pages**. 

When visitors land on your site, AERO will attempt to connect to **their** local Ollama instance (`http://localhost:11434`), letting them chat with their own local AI through your awesome 3D interface! *(Note: Agentic OS commands are disabled in Web Client Mode for security).*

### How to Deploy:
1. Initialize Git in this folder and push to a new GitHub repo:
   ```bash
   git init
   git add .
   git commit -m "Unleashing AERO"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/aero-jarvis-ai.git
   git push -u origin main
   ```
2. In your GitHub Repo, go to **Settings > Pages**.
3. Under **Build and deployment**, select the `main` branch and `/ (root)` folder.
4. Click **Save** and wait 2 minutes. Your site is live!

### ⚠️ Crucial Step for Visitors (Setting up Ollama)
For the web UI to talk to a local Ollama instance, Ollama needs to allow Cross-Origin Requests (CORS). Tell your visitors to run this before using the site:

**On Windows PowerShell:**
```powershell
$env:OLLAMA_ORIGINS="*"
ollama serve
```

---

<div align="center">
  <i>"At your service, Boss."</i>
</div>
