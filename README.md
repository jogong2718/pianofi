# AWS SSO Setup and project-aws Directory Creation

Before you begin, ensure you have AWS CLI installed and configured for SSO.

## 0. Configure AWS SSO

If you haven't already configured SSO, run the following command and follow the prompts:

```sh
aws configure sso
```

You will be asked for:
- SSO session name (i named it pianofi-app)
- SSO Start URL (it's in the email i sent yall)
- SSO Region (us-east-1)
- SSO registration scopes (sso:account:access)
- SSO Account ID (should be automatic)
- SSO Role Name (should be automatic)
- Default client region (ca-central-1)
- CLI default output format (used default json)
- CLI profile name (e.g., jonny-dev, choose your own {cli_p_name})

This will create a profile in your AWS CLI config for SSO authentication.

## 1. Log in to AWS SSO

Refresh your AWS SSO tokens by running:

```sh
aws sso login --profile {cli_p_name}
```

Replace {cli_p_name} with your AWS profile name.

## 2. Create the project-aws Directory Structure

In your project root, create the necessary directories for AWS SSO cache:

```sh
mkdir -p project-aws/sso/cache
```

## 3. Copy SSO Cache Files

Copy your AWS SSO cache files from your home directory to the project directory:

```sh
cp ~/.aws/sso/cache/* project-aws/sso/cache/
```

This ensures your project has access to the required SSO credentials.

## 4. Add AWS_PROFILE to env file in packages

Add your AWS profile name to the AWS_PROFILE parameter in the env file

---

You are now ready to use AWS resources with your project!
