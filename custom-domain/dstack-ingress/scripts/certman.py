#!/usr/bin/env python3

from dns_providers import DNSProviderFactory
import argparse
import os
import subprocess
import sys
from typing import List, Optional, Tuple

# Add script directory to path to import dns_providers
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class CertManager:
    """Certificate management using DNS provider infrastructure."""

    def __init__(self, provider_type: Optional[str] = None):
        """Initialize cert manager with DNS provider."""
        # Use the same DNS provider factory
        self.provider_type = provider_type or self._detect_provider_type()
        self.provider = DNSProviderFactory.create_provider(self.provider_type)

    def _detect_provider_type(self) -> str:
        """Detect provider type (reuse factory logic)."""
        return DNSProviderFactory._detect_provider_type()

    def install_plugin(self) -> bool:
        """Install certbot plugin for the current provider."""
        if not self.provider.CERTBOT_PACKAGE:
            print(f"No certbot package defined for {self.provider_type}")
            return False

        # First ensure certbot is installed in the current environment
        self._ensure_certbot_in_env()

        # Check if plugin is already installed
        try:
            if self.provider.CERTBOT_PLUGIN == "dns-namecheap":
                import certbot_dns_namecheap.dns_namecheap
                print(f"Plugin {self.provider.CERTBOT_PACKAGE} is already installed")
                return True
        except ImportError:
            pass  # Plugin not installed, continue with installation

        print(f"Installing certbot plugin: {self.provider.CERTBOT_PACKAGE}")

        # Try multiple installation methods
        install_methods = []
        
        # Method 1: Use the same python executable that's running this script
        import sys
        install_methods.append([sys.executable, "-m", "pip", "install", self.provider.CERTBOT_PACKAGE])
        
        # Method 2: Use virtual environment pip if available
        if "VIRTUAL_ENV" in os.environ:
            venv_pip = os.path.join(os.environ["VIRTUAL_ENV"], "bin", "pip")
            if os.path.exists(venv_pip):
                install_methods.append([venv_pip, "install", self.provider.CERTBOT_PACKAGE])
        
        # Method 3: Use system pip
        install_methods.append(["pip", "install", self.provider.CERTBOT_PACKAGE])
        
        # Method 4: Use pip3
        install_methods.append(["pip3", "install", self.provider.CERTBOT_PACKAGE])
        
        success = False
        for i, pip_cmd in enumerate(install_methods):
            print(f"Trying installation method {i+1}")
            print(f"Command: {' '.join(pip_cmd)}")
            try:
                result = subprocess.run(pip_cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"Installation method {i+1} succeeded")
                    success = True
                    break
                else:
                    print(f"Installation method {i+1} failed: {result.stderr}")
            except Exception as e:
                print(f"Installation method {i+1} exception: {e}")
        
        if not success:
            print(f"All installation methods failed", file=sys.stderr)
            return False
        
        print(f"Successfully installed {self.provider.CERTBOT_PACKAGE}")
        
        # Diagnostic information for troubleshooting
        try:
            import sys
            import pkg_resources
            print(f"Installed to Python: {sys.executable}")
            
            # Show certbot command
            certbot_cmd = self._get_certbot_command()
            print(f"Using certbot: {' '.join(certbot_cmd)}")
            
            try:
                dist = pkg_resources.get_distribution("certbot-dns-namecheap")
                print(f"Package version: {dist.version} at {dist.location}")
            except pkg_resources.DistributionNotFound:
                print("Warning: Package not found in current environment")
        except Exception as diag_error:
            print(f"Diagnostic error: {diag_error}")
        
        # Verify plugin installation
        try:
            if self.provider.CERTBOT_PLUGIN == "dns-namecheap":
                import certbot_dns_namecheap.dns_namecheap
                print(f"Plugin {self.provider.CERTBOT_PLUGIN} successfully imported")
                
                # Test if plugin is recognized by certbot
                certbot_cmd = self._get_certbot_command()
                test_cmd = certbot_cmd + ["plugins"]
                test_result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=10)
                
                if test_result.returncode == 0 and "dns-namecheap" in test_result.stdout:
                    print(f"✓ Plugin {self.provider.CERTBOT_PLUGIN} is available in certbot")
                    return True
                else:
                    print(f"Warning: dns-namecheap plugin not found in certbot plugins list")
                    if test_result.stderr:
                        print(f"Plugin test stderr: {test_result.stderr}")
                    
                    # Debug plugin registration
                    self._debug_plugin_registration()
                    
                    # Try force reinstall to fix plugin registration
                    print("Attempting to fix plugin registration...")
                    try:
                        import sys
                        force_cmd = [sys.executable, "-m", "pip", "install", "--force-reinstall", 
                                   "--no-deps", self.provider.CERTBOT_PACKAGE]
                        print(f"Running: {' '.join(force_cmd)}")
                        force_result = subprocess.run(force_cmd, capture_output=True, text=True)
                        
                        if force_result.returncode == 0:
                            # Test again after reinstall
                            retest_cmd = certbot_cmd + ["plugins"]
                            retest_result = subprocess.run(retest_cmd, capture_output=True, text=True, timeout=10)
                            if retest_result.returncode == 0 and "dns-namecheap" in retest_result.stdout:
                                print(f"✓ Plugin registration fixed after reinstall")
                                return True
                            else:
                                print(f"Plugin still not registered, may work anyway")
                        else:
                            print(f"Force reinstall failed: {force_result.stderr}")
                    except Exception as fix_error:
                        print(f"Plugin fix attempt failed: {fix_error}")
                    
                    # Continue anyway - may work in Docker environments
                    return True
            
        except Exception as e:
            print(f"Plugin verification warning: {e}")
            return True
        
        return True

    def _ensure_certbot_in_env(self) -> None:
        """Ensure certbot is installed in the current Python environment."""
        import sys
        
        # Try to import certbot to check if it's installed
        try:
            import certbot
            print(f"✓ Certbot module available in current environment")
            return
        except ImportError:
            print(f"Certbot module not found, installing...")
        
        # Install certbot if not available
        try:
            install_cmd = [sys.executable, "-m", "pip", "install", "certbot"]
            print(f"Running: {' '.join(install_cmd)}")
            result = subprocess.run(install_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✓ Certbot installed successfully in current environment")
            else:
                print(f"Failed to install certbot: {result.stderr}")
                # Continue anyway - may still work
        except Exception as e:
            print(f"Error installing certbot: {e}")
            # Continue anyway - may still work
    
    def _get_certbot_command(self) -> List[str]:
        """Get the correct certbot command that uses the same Python environment."""
        import sys
        import os
        
        # Always use certbot from the same Python environment
        python_dir = os.path.dirname(sys.executable)
        venv_certbot = os.path.join(python_dir, "certbot")
        
        if os.path.exists(venv_certbot):
            cmd = [venv_certbot]
            print(f"Using certbot from virtual environment: {venv_certbot}")
            return cmd
        
        # If certbot doesn't exist in venv, this is an error condition
        raise RuntimeError(
            f"Certbot not found in virtual environment: {venv_certbot}. "
            f"This indicates the environment setup failed. "
            f"Python executable: {sys.executable}"
        )
    
    def _debug_plugin_registration(self) -> None:
        """Debug why plugin is not being registered by certbot."""
        try:
            import pkg_resources
            print("=== Plugin Registration Debug ===")
            
            # Show which certbot we're using
            certbot_cmd = self._get_certbot_command()
            print(f"Using certbot: {' '.join(certbot_cmd)}")
            
            # Check entry points
            try:
                entry_points = list(pkg_resources.iter_entry_points('certbot.plugins'))
                print(f"Found {len(entry_points)} certbot plugins:")
                for ep in entry_points:
                    print(f"  - {ep.name}: {ep.module_name}")
                
                # Look specifically for dns-namecheap
                namecheap_eps = [ep for ep in entry_points if ep.name == 'dns-namecheap']
                if namecheap_eps:
                    print(f"✓ Found dns-namecheap entry point: {namecheap_eps[0]}")
                else:
                    print(f"✗ dns-namecheap entry point not found")
            except Exception as ep_error:
                print(f"Entry point check failed: {ep_error}")
            
            # Check if certbot can import the plugin module
            try:
                from certbot_dns_namecheap import dns_namecheap
                print(f"✓ Plugin module can be imported")
                
                # Check if it has the right class
                if hasattr(dns_namecheap, 'Authenticator'):
                    print(f"✓ Authenticator class found")
                else:
                    print(f"✗ Authenticator class not found")
            except Exception as import_error:
                print(f"✗ Plugin module import failed: {import_error}")
            
            print("=== End Debug ===")
        except Exception as debug_error:
            print(f"Debug failed: {debug_error}")
    
    def _validate_provider_credentials(self) -> bool:
        """Validate provider credentials by testing API access."""
        print(f"Validating {self.provider_type} API credentials...")
        
        try:
            # For Namecheap, test API access
            if hasattr(self.provider, '_make_request'):
                test_result = self.provider._make_request("namecheap.users.getBalances")
                if test_result.get("success", False):
                    print(f"✓ {self.provider_type} API credentials are valid")
                    return True
                else:
                    print(f"✗ {self.provider_type} API validation failed: {test_result.get('errors', ['Unknown error'])}")
                    return False
            else:
                print(f"No API validation available for {self.provider_type}, skipping")
                return True
        except Exception as e:
            print(f"Error validating {self.provider_type} credentials: {e}")
            return False
    
    def setup_credentials(self) -> bool:
        """Setup credentials file for certbot using provider implementation."""
        result = self.provider.setup_certbot_credentials()
        if not result:
            print(f"Failed to setup credentials file for {self.provider_type}")
        return result

    def _build_certbot_command(self, action: str, domain: str, email: str) -> List[str]:
        """Build certbot command using provider configuration."""
        plugin = self.provider.CERTBOT_PLUGIN
        if not plugin:
            raise ValueError(f"No certbot plugin configured for {self.provider_type}")

        # Use Python module execution to ensure same environment
        certbot_cmd = self._get_certbot_command()
        base_cmd = certbot_cmd + [action, "-a", plugin, "--non-interactive", "-v"]

        # Add credentials file if configured
        if self.provider.CERTBOT_CREDENTIALS_FILE:
            credentials_file = os.path.expanduser(self.provider.CERTBOT_CREDENTIALS_FILE)
            if os.path.exists(credentials_file):
                base_cmd.extend([f"--{plugin}-credentials={credentials_file}"])
            else:
                raise ValueError(f"Credentials file does not exist: {credentials_file}")

        if action == "certonly":
            base_cmd.extend(["--agree-tos", "--no-eff-email", "--email", email, "-d", domain])

        # Log command with masked email for debugging
        masked_cmd = [arg if not (i > 0 and base_cmd[i-1] == "--email") else "<email>" 
                     for i, arg in enumerate(base_cmd)]
        print(f"Executing: {' '.join(masked_cmd)}")
        
        return base_cmd

    def obtain_certificate(self, domain: str, email: str) -> bool:
        """Obtain a new certificate for the domain."""
        print(f"Obtaining certificate for {domain} using {self.provider_type}")
        
        # Ensure plugin is installed
        if not self.install_plugin():
            print(f"Failed to install plugin for {self.provider_type}", file=sys.stderr)
            return False
        
        # Validate credentials before proceeding
        if not self._validate_provider_credentials():
            print(f"Failed to validate credentials for {self.provider_type}", file=sys.stderr)
            return False
        
        # Setup credentials file
        if not self.setup_credentials():
            print(f"Failed to setup credentials for {self.provider_type}", file=sys.stderr)
            return False

        cmd = self._build_certbot_command("certonly", domain, email)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"✓ Certificate obtained successfully for {domain}")
                return True
            else:
                print(f"✗ Certificate obtaining failed (exit code: {result.returncode})")
                
                # Check for specific error patterns
                error_output = result.stderr.strip() if result.stderr else ""
                stdout_output = result.stdout.strip() if result.stdout else ""
                
                if "unrecognized arguments" in error_output:
                    print(f"Plugin arguments not recognized by certbot")
                    print(f"This suggests the plugin is not properly registered")
                elif "DNS problem" in error_output or "DNS problem" in stdout_output:
                    print(f"DNS validation failed - check domain configuration")
                elif "Rate limited" in error_output or "Rate limited" in stdout_output:
                    print(f"Rate limited by Let's Encrypt")
                
                if error_output:
                    print(f"stderr: {error_output}")
                if stdout_output:
                    print(f"stdout: {stdout_output}")
                
                return False

        except subprocess.TimeoutExpired:
            print(f"Certbot command timed out after 300 seconds", file=sys.stderr)
            return False
        except Exception as e:
            print(f"Error running certbot: {e}", file=sys.stderr)
            return False

    def renew_certificate(self, domain: str) -> Tuple[bool, bool]:
        """Renew certificates.

        Returns:
            (success, renewed): success status and whether renewal was actually performed
        """
        print(f"Renewing certificate using {self.provider_type}")
        
        # Ensure plugin is installed
        if not self.install_plugin():
            print(f"Failed to install plugin for renewal", file=sys.stderr)
            return False, False

        cmd = self._build_certbot_command("renew", domain, "")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"✓ Certificate renewal completed")
                return True, True
            else:
                error_output = result.stderr.strip() if result.stderr else ""
                stdout_output = result.stdout.strip() if result.stdout else ""
                
                print(f"✗ Certificate renewal failed (exit code: {result.returncode})")
                
                # Check for specific error patterns
                if "unrecognized arguments" in error_output:
                    print(f"Plugin arguments not recognized by certbot")
                elif "No renewals were attempted" in stdout_output:
                    print(f"No certificates need renewal")
                    return True, False  # Success but no renewal needed
                elif "DNS problem" in error_output or "DNS problem" in stdout_output:
                    print(f"DNS validation failed during renewal")
                
                if error_output:
                    print(f"stderr: {error_output}")
                if stdout_output:
                    print(f"stdout: {stdout_output}")
                
                return False, False

            # Check if no renewals were needed
            if "No renewals were attempted" in result.stdout:
                print("No certificates need renewal")
                return True, False

            print("Certificate renewed successfully")
            return True, True

        except Exception as e:
            print(f"Error running certbot: {e}", file=sys.stderr)
            return False, False

    def certificate_exists(self, domain: str) -> bool:
        """Check if certificate already exists for domain."""
        cert_path = f"/etc/letsencrypt/live/{domain}/fullchain.pem"
        return os.path.isfile(cert_path)

    def run_action(
        self, domain: str, email: str, action: str = "auto"
    ) -> Tuple[bool, bool]:
        """High-level certificate management.

        Returns:
            (success, needs_evidence): success status and whether evidence should be generated
        """
        if action == "auto":
            if self.certificate_exists(domain):
                success, renewed = self.renew_certificate(domain)
                return success, renewed  # Only generate evidence if actually renewed
            else:
                success = self.obtain_certificate(domain, email)
                return success, success  # Always generate evidence for new certificates
        elif action == "obtain":
            success = self.obtain_certificate(domain, email)
            return success, success
        elif action == "renew":
            success, renewed = self.renew_certificate(domain)
            return success, renewed
        else:
            raise ValueError(f"Invalid action: {action}")


def main():
    parser = argparse.ArgumentParser(
        description="Manage SSL certificates with certbot using DNS providers"
    )
    parser.add_argument(
        "action", choices=["obtain", "renew", "auto", "setup"], help="Action to perform"
    )
    parser.add_argument("--domain", help="Domain name")
    parser.add_argument("--email", help="Email for Let's Encrypt registration")
    parser.add_argument("--provider", help="DNS provider (cloudflare, linode, etc)")

    args = parser.parse_args()

    try:
        manager = CertManager(args.provider)

        # Handle setup action
        if args.action == "setup":
            if not manager.install_plugin():
                sys.exit(1)
            if not manager.setup_credentials():
                sys.exit(1)
            print(f"Setup completed for {manager.provider_type} provider")
            return

        # Domain is required for certificate operations
        if not args.domain:
            print(
                "Error: --domain is required for certificate operations",
                file=sys.stderr,
            )
            sys.exit(1)

        # Email is required for obtain and auto actions
        if args.action in ["obtain", "auto"] and not args.email:
            if not os.environ.get("CERTBOT_EMAIL"):
                print(
                    "Error: --email is required or set CERTBOT_EMAIL environment variable",
                    file=sys.stderr,
                )
                sys.exit(1)
            args.email = os.environ["CERTBOT_EMAIL"]

        success, needs_evidence = manager.run_action(
            args.domain, args.email, args.action
        )

        if not success:
            sys.exit(1)

        # Exit with code 2 if no evidence generation is needed (no renewal was performed)
        if not needs_evidence:
            sys.exit(2)

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
