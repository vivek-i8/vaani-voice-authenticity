# 🖱️ Ultra-Detailed VAANI Deployment Guide - Step 3 Onwards

## 🔧 STEP 3: CONNECT TO EC2 INSTANCE

### 3.1 Find Your Instance Details
1. **Go back to EC2 console** (if you navigated away)
2. In left menu, click **"Instances"** (under "Instances" section)
3. **Find your instance** named `vaani-backend-server` in the list
4. **Select the checkbox** next to your instance
5. **Look at the "Details" tab** (bottom panel)
6. **Find the "Public IPv4 address"** field
7. **Copy the IP address** (e.g., 3.85.123.45) - you'll need this for SSH

### 3.2 Connect via SSH (Windows Users)
1. **Open PowerShell** or **Command Prompt**
2. **Navigate to your Downloads folder** (where .pem file was saved):
   ```
   cd Downloads
   ```
3. **Set permissions for the key file**:
   ```
   icacls vaani-ec2-key.pem /inheritance:r
   icacls vaani-ec2-key.pem /grant:r "%USERNAME%:(R)"
   ```
4. **Connect to your EC2 instance**:
   ```
   ssh -i vaani-ec2-key.pem ubuntu@YOUR_PUBLIC_IP
   ```
   (Replace YOUR_PUBLIC_IP with the IP you copied)

### 3.2 Connect via SSH (Mac/Linux Users)
1. **Open Terminal**
2. **Navigate to your Downloads folder**:
   ```
   cd Downloads
   ```
3. **Set permissions for the key file**:
   ```
   chmod 400 vaani-ec2-key.pem
   ```
4. **Connect to your EC2 instance**:
   ```
   ssh -i vaani-ec2-key.pem ubuntu@YOUR_PUBLIC_IP
   ```
   (Replace YOUR_PUBLIC_IP with the IP you copied)

### 3.3 Verify Connection
1. **You should see** a welcome message: "Welcome to Ubuntu 22.04 LTS"
2. **Your command prompt** should now show: `ubuntu@ip-xxx-xx-xx-xxx:~$`
3. **You are now connected** to your EC2 instance!

## 🛠️ STEP 4: SETUP EC2 SERVER ENVIRONMENT

### 4.1 Update System Packages
1. **Type the following command** and press Enter:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
2. **Wait for updates** to complete (may take 2-5 minutes)
3. **You will see** "Upgrade complete" when finished

### 4.2 Install Python and System Dependencies
1. **Install Python 3.10**:
   ```bash
   sudo apt install python3.10 python3.10-venv python3.10-dev -y
   ```
2. **Install audio processing libraries**:
   ```bash
   sudo apt install ffmpeg libsndfile1 -y
   ```
3. **Install Node.js** (needed for some build processes):
   ```bash
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt install nodejs -y
   ```
4. **Verify installations**:
   ```bash
   python3.10 --version
   node --version
   npm --version
   ```

### 4.3 Clone and Setup VAANI Application
1. **Clone the repository**:
   ```bash
   git clone https://github.com/vivek-i8/vaani-voice-authenticity.git
   ```
2. **Navigate to project directory**:
   ```bash
   cd vaani-voice-authenticity
   ```
3. **Create Python virtual environment**:
   ```bash
   python3.10 -m venv venv
   ```
4. **Activate virtual environment**:
   ```bash
   source venv/bin/activate
   ```
5. **Your prompt should now show**: `(venv) ubuntu@ip-xxx-xx-xx-xxx:~/vaani-voice-authenticity$`

### 4.4 Install Python Dependencies
1. **Install required packages**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Wait for installation** to complete (may take 5-10 minutes)
3. **You will see** "Successfully installed" messages

### 4.5 Create Environment Configuration File
1. **Create the .env file**:
   ```bash
   nano .env
   ```
2. **Copy and paste these exact lines** (use right-click to paste in SSH):
   ```env
   MODEL_NAME=Gustking/wav2vec2-large-xlsr-deepfake-audio-classification
   CONFIDENCE_THRESHOLD=0.6
   MIN_AUDIO_DURATION=3.0
   MAX_AUDIO_DURATION=5.0
   SAMPLE_RATE=16000
   MAX_CLIPS=10
   USE_BEDROCK=true
   AWS_REGION=us-east-1
   BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
   ```
3. **Save the file**:
   - Press **Ctrl+X**
   - Press **Y** (for Yes)
   - Press **Enter** (to confirm filename)
4. **Verify file was created**:
   ```bash
   cat .env
   ```

### 4.6 Setup System Service for Auto-Startup
1. **Create the service file**:
   ```bash
   sudo nano /etc/systemd/system/vaani-backend.service
   ```
2. **Copy and paste these exact lines**:
   ```ini
   [Unit]
   Description=VAANI Backend API
   After=network.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/vaani-voice-authenticity
   Environment=PATH=/home/ubuntu/vaani-voice-authenticity/venv/bin
   ExecStart=/home/ubuntu/vaani-voice-authenticity/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
3. **Save the file**:
   - Press **Ctrl+X**
   - Press **Y**
   - Press **Enter**

### 4.7 Start the Backend Service
1. **Enable the service** (start on boot):
   ```bash
   sudo systemctl enable vaani-backend
   ```
2. **Start the service**:
   ```bash
   sudo systemctl start vaani-backend
   ```
3. **Check service status**:
   ```bash
   sudo systemctl status vaani-backend
   ```
4. **You should see** "active (running)" in green text
5. **Press Q** to exit the status view
6. **Test the API**:
   ```bash
   curl http://localhost:8000/health
   ```
   (You should see: {"status": "healthy", "timestamp": "..."} )

## 🤖 STEP 5: CONFIGURE AWS BEDROCK

### 5.1 Navigate to Bedrock Console
1. **Open a new browser tab** (keep SSH connection open)
2. **Go to AWS Console**: https://console.aws.amazon.com
3. **In the search bar** (top center), type **"Bedrock"**
4. **Click on "Bedrock"** from the dropdown results
5. **If first time**, click **"Get started"** button

### 5.2 Request Model Access
1. **In the left navigation menu**, click **"Model access"**
2. **Click the blue "Edit" button** (top right corner)
3. **Scroll down** to find the **"Anthropic"** section
4. **Check the box** next to **"Claude 3.5 Sonnet"**
5. **Scroll to the bottom** and click **"Save changes"**
6. **Wait for access** - status should change from "Pending" to "Access granted" (usually within 1-2 minutes)

### 5.3 Create IAM Role for Bedrock Access
1. **In the AWS search bar**, type **"IAM"**
2. **Click on "IAM"** from dropdown
3. **In the left menu**, click **"Roles"** (under "Access management")
4. **Click the blue "Create role" button** (top right)
5. **Trusted entity type**: Select **"AWS service"**
6. **Use case**: Select **"EC2"** from the dropdown
7. **Click the blue "Next" button** (bottom right)
8. **In the "Permissions policies" search box**, type **"Bedrock"**
9. **Check the box** next to **"AmazonBedrockFullAccess"**
10. **Click the blue "Next" button**
11. **Role name**: Type `EC2-Bedrock-Role`
12. **Description**: Type `Role for EC2 instance to access AWS Bedrock`
13. **Click the blue "Create role" button**

### 5.4 Attach IAM Role to EC2 Instance
1. **Go back to EC2 console** (search for "EC2")
2. **In left menu**, click **"Instances"**
3. **Select your instance** `vaani-backend-server` by clicking the checkbox
4. **Click the "Actions" button** (top right)
5. **Hover over "Security"** in the dropdown
6. **Click "Modify IAM role"**
7. **In the "IAM role" dropdown**, select **"EC2-Bedrock-Role"**
8. **Click the blue "Update IAM role" button**
9. **You should see** a success message: "IAM role updated successfully"

## 🌐 STEP 6: SETUP NGINX REVERSE PROXY

### 6.1 Install Nginx
1. **Go back to your SSH terminal** (should still be connected to EC2)
2. **Install Nginx**:
   ```bash
   sudo apt install nginx -y
   ```
3. **Check Nginx status**:
   ```bash
   sudo systemctl status nginx
   ```
4. **Press Q** to exit status view

### 6.2 Configure Nginx Virtual Host
1. **Create Nginx configuration file**:
   ```bash
   sudo nano /etc/nginx/sites-available/vaani
   ```
2. **Copy and paste these exact lines** (replace YOUR_PUBLIC_IP with your actual EC2 IP):
   ```nginx
   server {
       listen 80;
       server_name YOUR_PUBLIC_IP;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```
3. **Important**: Replace `YOUR_PUBLIC_IP` with your actual EC2 public IP address
4. **Save the file**:
   - Press **Ctrl+X**
   - Press **Y**
   - Press **Enter**

### 6.3 Enable Nginx Configuration
1. **Enable the site**:
   ```bash
   sudo ln -s /etc/nginx/sites-available/vaani /etc/nginx/sites-enabled/
   ```
2. **Test Nginx configuration**:
   ```bash
   sudo nginx -t
   ```
3. **You should see**: "syntax is ok" and "test is successful"
4. **Restart Nginx**:
   ```bash
   sudo systemctl restart nginx
   ```
5. **Enable Nginx to start on boot**:
   ```bash
   sudo systemctl enable nginx
   ```
6. **Check Nginx status**:
   ```bash
   sudo systemctl status nginx
   ```
7. **Press Q** to exit

## 🚀 STEP 7: DEPLOY FRONTEND TO VERCEL

### 7.1 Prepare GitHub Repository
1. **On your local computer** (not EC2), open a terminal/command prompt
2. **Navigate to your VAANI project folder**
3. **Initialize git repository** (if not already done):
   ```bash
   git init
   ```
4. **Create GitHub repository**:
   - Go to https://github.com
   - Click **"+"** (top right) → **"New repository"**
   - **Repository name**: `vaani-voice-authenticity`
   - **Description**: `AI Voice Authenticity Detection System`
   - **Select "Public"**
   - **Check "Add a README file"**
   - Click **"Create repository"**
5. **Copy the repository URL** (e.g., `https://github.com/YOUR_USERNAME/vaani-voice-authenticity.git`)

### 7.2 Push Code to GitHub
1. **In your local terminal**:
   ```bash
   git add .
   git commit -m "Initial commit - VAANI voice authenticity system"
   git remote add origin https://github.com/YOUR_USERNAME/vaani-voice-authenticity.git
   git branch -M main
   git push -u origin main
   ```
2. **Enter your GitHub credentials** if prompted

### 7.3 Deploy to Vercel
1. **Go to https://vercel.com**
2. **Click "Sign Up"** or **"Login"**
3. **Click "Continue with GitHub"**
4. **Authorize Vercel** to access your GitHub account
5. **Click "New Project"** button (top right)
6. **Find and select** your `vaani-voice-authenticity` repository
7. **Click "Import"**
8. **Configure deployment settings**:
   - **Framework Preset**: Select **"Other"**
   - **Root Directory**: Type `frontend`
   - **Build Command**: Type `npm run build`
   - **Output Directory**: Type `dist`
   - **Install Command**: Type `npm install`
   - **Node.js Version**: Select **"18.x"**
9. **Add Environment Variables**:
   - **Click "Add Environment Variable"**
   - **Name**: `VITE_API_URL`
   - **Value**: `http://YOUR_EC2_PUBLIC_IP:8000`
   - **Click "Add"**
10. **Click the blue "Deploy" button**
11. **Wait for deployment** (may take 2-5 minutes)
12. **Once deployed**, copy your Vercel URL (e.g., `https://vaani-voice-authenticity.vercel.app`)

## 🧪 STEP 8: TEST THE COMPLETE DEPLOYMENT

### 8.1 Test Backend API
1. **In your browser**, go to `http://YOUR_EC2_IP:8000/docs`
2. **You should see** FastAPI interactive documentation
3. **Test the health endpoint**:
   - Click **"GET /health"**
   - Click **"Try it out"**
   - Click **"Execute"**
   - **You should see**: `{"status": "healthy", "timestamp": "..."}`

### 8.2 Test Frontend
1. **Go to your Vercel URL** (from Step 7.3)
2. **The VAANI application should load**
3. **Try uploading an audio file** (any .wav or .mp3 file)
4. **Check if the upload processes** and returns results

### 8.3 Test End-to-End Integration
1. **Upload a voice sample** through the Vercel frontend
2. **Verify the request goes** to your EC2 backend
3. **Check if AWS Bedrock** generates explanations
4. **Confirm results display** properly in the frontend

### 8.4 Troubleshooting Common Issues
1. **If backend fails**:
   - Check service status: `sudo systemctl status vaani-backend`
   - View logs: `sudo journalctl -u vaani-backend -f`
   
2. **If frontend can't connect to backend**:
   - Verify Nginx is running: `sudo systemctl status nginx`
   - Check security groups in AWS EC2 console
   
3. **If Bedrock doesn't work**:
   - Verify model access in Bedrock console
   - Check IAM role attachment in EC2 console

## 📊 STEP 9: MONITORING AND MAINTENANCE

### 9.1 Check Service Status
1. **SSH into your EC2 instance** if disconnected
2. **Check all services**:
   ```bash
   sudo systemctl status vaani-backend
   sudo systemctl status nginx
   ```
3. **Press Q** to exit each status view

### 9.2 View Logs
1. **Backend logs**:
   ```bash
   sudo journalctl -u vaani-backend -f
   ```
2. **Nginx access logs**:
   ```bash
   sudo tail -f /var/log/nginx/access.log
   ```
3. **Nginx error logs**:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```
4. **Press Ctrl+C** to stop viewing logs

### 9.3 Monitor AWS Costs
1. **In AWS Console**, click your name (top right)
2. **Click "My Billing Dashboard"**
3. **Monitor your $200 credit usage**
4. **Set up billing alerts** if desired

## 🔄 STEP 10: UPDATES AND MAINTENANCE

### 10.1 Update Application Code
1. **Make changes** to your local code
2. **Commit and push** to GitHub:
   ```bash
   git add .
   git commit -m "Update application"
   git push origin main
   ```
3. **Vercel will auto-redeploy** the frontend
4. **For backend updates**, SSH into EC2:
   ```bash
   cd ~/vaani-voice-authenticity
   git pull origin main
   source venv/bin/activate
   pip install -r requirements.txt
   sudo systemctl restart vaani-backend
   ```

### 10.2 Backup Important Data
1. **Create backup script**:
   ```bash
   nano backup.sh
   ```
2. **Add backup commands**:
   ```bash
   #!/bin/bash
   tar -czf /home/ubuntu/vaani-backup-$(date +%Y%m%d).tar.gz /home/ubuntu/vaani-voice-authenticity
   ```
3. **Make it executable**:
   ```bash
   chmod +x backup.sh
   ```

## 🎉 DEPLOYMENT COMPLETE!

Your VAANI voice authenticity detection system is now fully deployed with:
- ✅ **Backend** running on AWS EC2 with FastAPI + PyTorch
- ✅ **Frontend** deployed on Vercel with React
- ✅ **AWS Bedrock** integration for explainability
- ✅ **Nginx** reverse proxy for production-ready setup
- ✅ **Auto-restart** services for reliability

**Monthly estimated cost**: $50-120 (well within your $200 AWS credit)

**Next Steps**:
1. Monitor system performance
2. Set up additional monitoring if needed
3. Consider SSL certificate setup for HTTPS
4. Scale up instance type if traffic increases

**Support**: If you encounter any issues, check the troubleshooting section in Step 8.4.
