# Google OAuth Testing Mode Setup

## 🚨 Issue: "Access blocked: SakeMonkeyRecipeDB has not completed the Google verification process"

This is a common issue when using Google OAuth with a new application. Here's how to fix it:

## 🔧 Solution: Enable Testing Mode

### Step 1: Go to Google Cloud Console
1. **Visit**: https://console.cloud.google.com/
2. **Select your project** (the one you created for SakeMonkeyRecipeDB)

### Step 2: Configure OAuth Consent Screen
1. **Go to**: "APIs & Services" > "OAuth consent screen"
2. **Click**: "Edit App" (or "Create" if not created yet)

### Step 3: Set Up Testing Mode
1. **User Type**: Choose "External" (unless you have a Google Workspace)
2. **App Information**:
   - App name: `SakeMonkeyRecipeDB`
   - User support email: Your email
   - Developer contact: Your email
3. **Scopes**: Add `https://www.googleapis.com/auth/spreadsheets`
4. **Test users**: Add your email address
5. **Publishing status**: Keep as "Testing"

### Step 4: Add Test Users
1. **In OAuth consent screen**:
   - Scroll down to "Test users"
   - Click "Add users"
   - Add your email address
   - Add any other users you want to test with
2. **Save** the configuration

### Step 5: Update OAuth Settings
1. **Go to**: "APIs & Services" > "Credentials"
2. **Click on your OAuth 2.0 Client ID**
3. **Authorized redirect URIs**: Add `http://localhost:58384/`
4. **Save** the changes

## 🔄 Alternative: Use Service Account (Recommended)

If OAuth continues to be problematic, we can use a Service Account instead:

### Step 1: Create Service Account
1. **Go to**: "APIs & Services" > "Credentials"
2. **Click**: "Create Credentials" > "Service Account"
3. **Name**: `SakeMonkeyRecipeDB-Service`
4. **Description**: `Service account for SakeMonkey Recipe Database`
5. **Click**: "Create and Continue"

### Step 2: Create Service Account Key
1. **Click on the service account** you just created
2. **Go to**: "Keys" tab
3. **Click**: "Add Key" > "Create new key"
4. **Type**: JSON
5. **Click**: "Create"
6. **Download** the JSON file
7. **Rename** it to `service_account.json`
8. **Place** it in your project directory

### Step 3: Share Google Sheet with Service Account
1. **Open your Google Sheet**: https://docs.google.com/spreadsheets/d/1dp-fcWV0Mm0audZm-EAsQOjyh-C3f6f6
2. **Click**: "Share" button
3. **Add email**: The service account email (found in the JSON file)
4. **Permission**: "Editor"
5. **Click**: "Send"

## 🛠️ Updated Setup Script

I'll create an updated setup script that handles both OAuth and Service Account methods:

```python
# This will be created in the next step
```

## 🎯 Quick Fix Options

### Option 1: OAuth Testing Mode (Easiest)
- Follow steps 1-5 above
- Add your email as a test user
- Try the OAuth flow again

### Option 2: Service Account (Most Reliable)
- Create service account
- Download JSON key
- Share Google Sheet with service account
- Use service account authentication

### Option 3: Use Existing Credentials
- If you have an existing Google Cloud project
- Use those credentials instead
- Update the client ID in the OAuth flow

## 🔍 Troubleshooting

### If you still get "Access blocked":
1. **Check test users**: Make sure your email is added
2. **Check scopes**: Ensure spreadsheets scope is added
3. **Check redirect URI**: Must match exactly
4. **Wait a few minutes**: Changes can take time to propagate

### If OAuth doesn't work at all:
1. **Use Service Account method** (most reliable)
2. **Check Google Cloud Console** for any errors
3. **Verify API is enabled**: Google Sheets API must be enabled

## 📞 Need Help?

If you're still having issues:
1. **Check Google Cloud Console** for error messages
2. **Verify your Google account** has proper permissions
3. **Try the Service Account method** as it's more reliable
4. **Check the Google Cloud Console logs** for detailed error information

The Service Account method is usually more reliable for personal projects and doesn't require OAuth verification.



