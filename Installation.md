# Installation Guide

## Prerequisites

### Checkmk Server
- Checkmk 2.4.0p1 or later (Cloud, Enterprise, or Raw Edition)
- Network access to the SEP Sesam server on port 11401 (HTTPS)

### SEP Sesam Server
- REST API accessible (default port: 11401)
- User account with REST API access permissions

## Step 1: Install the Plugin

Copy the MKP file to your Checkmk server and switch to the site user:

```bash
scp sep_sesam-1.0.0.mkp user@checkmk-server:/tmp/
ssh user@checkmk-server
sudo su - <sitename>
```

Install and enable the plugin:

```bash
mkp add /tmp/sep_sesam-1.0.0.mkp
mkp enable sep_sesam 1.0.0
```

Restart Apache to load the new rulesets:

```bash
omd restart apache
```

Verify the installation:

```bash
mkp list
# Should show: sep_sesam 1.0.0
```

## Step 2: Add the SEP Sesam Host to Checkmk

1. Go to **Setup > Hosts > Add host**
2. Enter the SEP Sesam server hostname or IP
3. Set the monitoring agent to **"No API integrations, no Checkmk agent"**
4. Save the host

## Step 3: Store Password in Password Store (Recommended)

1. Go to **Setup > General > Passwords**
2. Click **Add password**
3. Configure:
   - **Unique ID**: `sep_sesam_api` (or similar)
   - **Title**: `SEP Sesam REST API`
   - **Password**: Enter the SEP Sesam user password
4. Save

## Step 4: Configure the Special Agent

1. Go to **Setup > Agents > Other integrations > Storage > SEP Sesam Backup Server**
2. Click **Add rule**
3. Configure the connection:

| Setting | Value |
|---------|-------|
| **API Port** | 11401 (default) |
| **Username** | SEP Sesam API username |
| **Password** | Select from password store |
| **Verify SSL** | Disable if using a self-signed certificate |
| **Backup Groups** | Leave empty to auto-discover, or list specific group names |
| **Datastores** | Leave empty to auto-discover, or list specific datastore names |

4. Set **Explicit hosts** to your SEP Sesam server hostname
5. Save the rule

## Step 5: Run Service Discovery

1. Go to your SEP Sesam host in Checkmk
2. Click **Run service discovery**
3. Accept the discovered services
4. Activate changes

Expected services after discovery:

| Service | Status |
|---------|--------|
| SEP Sesam Backup Group Daily | OK |
| SEP Sesam Datastore DS1 | OK |
| SEP Sesam License | OK |

## Step 6: Test the Special Agent (Optional)

Run the agent manually as the site user to verify connectivity:

```bash
echo 'mypassword' | \
  local/lib/python3/cmk_addons/plugins/sep_sesam/libexec/agent_sep_sesam \
  --hostname sesam-server.local \
  --username admin \
  --no-verify-ssl
```

## Troubleshooting

### "Connection refused" or timeout

1. Check firewall: port 11401 must be open from Checkmk to SEP Sesam
2. Test connectivity:
   ```bash
   curl -k https://sesam-server:11401/sep/api/v2/backupgroups
   ```

### "401 Unauthorized"

1. Verify the username and password
2. Test authentication manually:
   ```bash
   curl -k -u username:password https://sesam-server:11401/sep/api/v2/backupgroups
   ```

### "SSL certificate verify failed"

Enable **"Disable SSL certificate verification"** in the special agent rule, or install
the SEP Sesam server certificate as trusted on the Checkmk server.

### No services discovered

1. Check the special agent output: run the agent manually (see Step 6)
2. Verify the SEP Sesam server has backup groups and datastores configured
3. Check that the user account has sufficient permissions

## Upgrading

```bash
mkp add sep_sesam-X.Y.Z.mkp
mkp disable sep_sesam 1.0.0
mkp enable sep_sesam X.Y.Z
omd restart apache
cmk -R
```

## Uninstalling

```bash
mkp disable sep_sesam 1.0.0
mkp remove sep_sesam 1.0.0
omd restart apache
```

Remove the special agent rule under **Setup > Agents > Other integrations** and
re-discover services on the affected host.
