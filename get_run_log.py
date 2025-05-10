#!/usr/bin/env python3
import subprocess
import argparse
import json
import datetime
import os
import re
import time
import sys
from pathlib import Path


class CloudRunLogFetcher:
    def __init__(self, project_id=None, service=None, region=None, output_dir=None, gcloud_path=None):
        """Initialize the log fetcher with service details."""
        self.project_id = project_id
        self.service = service
        self.region = region
        self.gcloud_path = gcloud_path or self._find_gcloud_executable()
        
        if not self.gcloud_path:
            print("ERROR: gcloud executable not found. Please provide its path with --gcloud-path")
            print("       or ensure it's in your system PATH.")
            print("       You can download gcloud CLI from: https://cloud.google.com/sdk/docs/install")
            sys.exit(1)
        
        # Set default output directory if not provided
        if output_dir:
            self.output_dir = output_dir
        else:
            home_dir = str(Path.home())
            self.output_dir = os.path.join(home_dir, "cloud_run_logs")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"Using gcloud at: {self.gcloud_path}")
    
    def _find_gcloud_executable(self):
        """Find the gcloud executable path."""
        # Check common installation paths on Windows
        windows_paths = [
            os.path.expanduser("~\\AppData\\Local\\Google\\Cloud SDK\\google-cloud-sdk\\bin\\gcloud.cmd"),
            os.path.expanduser("~\\google-cloud-sdk\\bin\\gcloud.cmd"),
            "C:\\Program Files\\Google\\Cloud SDK\\google-cloud-sdk\\bin\\gcloud.cmd",
            "C:\\Program Files (x86)\\Google\\Cloud SDK\\google-cloud-sdk\\bin\\gcloud.cmd",
        ]
        
        # Check common installation paths on Unix/Linux/Mac
        unix_paths = [
            "/usr/bin/gcloud",
            "/usr/local/bin/gcloud",
            os.path.expanduser("~/google-cloud-sdk/bin/gcloud"),
        ]
        
        # Try to find in PATH first
        try:
            # On Windows, we need to check for gcloud.cmd or gcloud.bat
            if os.name == 'nt':
                for ext in ['.cmd', '.bat', '.exe', '']:
                    try:
                        path = subprocess.check_output(['where', f'gcloud{ext}'], 
                                                     stderr=subprocess.DEVNULL,
                                                     universal_newlines=True).strip()
                        if path:
                            return path.split('\n')[0]  # Use first result
                    except subprocess.CalledProcessError:
                        continue
                
                # Check common Windows installation paths
                for path in windows_paths:
                    if os.path.exists(path):
                        return path
            else:
                # On Unix-like systems
                path = subprocess.check_output(['which', 'gcloud'], 
                                             stderr=subprocess.DEVNULL,
                                             universal_newlines=True).strip()
                if path:
                    return path
                
                # Check common Unix installation paths
                for path in unix_paths:
                    if os.path.exists(path):
                        return path
                        
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        return None
    
    def run_gcloud_command(self, args, check=True, capture_output=True, text=True, shell=False):
        """Run a gcloud command with proper error handling."""
        cmd = [self.gcloud_path] + args
        
        try:
            if shell:
                cmd_str = ' '.join(cmd)
                return subprocess.run(cmd_str, shell=True, check=check, 
                                     capture_output=capture_output, text=text)
            else:
                return subprocess.run(cmd, check=check, capture_output=capture_output, text=text)
        except FileNotFoundError:
            print(f"ERROR: Could not execute gcloud command. Make sure the path is correct: {self.gcloud_path}")
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            print(f"ERROR: gcloud command failed: {e}")
            if e.stderr:
                print(f"Details: {e.stderr}")
            if not check:
                return e
            sys.exit(1)
    
    def get_project_id(self):
        """Get the current project ID if not specified."""
        if self.project_id:
            return self.project_id
        
        try:
            result = self.run_gcloud_command(["config", "get-value", "project"])
            project_id = result.stdout.strip()
            
            if not project_id or project_id == "(unset)":
                print("ERROR: No project ID set. Please specify with --project or set with:")
                print("       gcloud config set project YOUR_PROJECT_ID")
                sys.exit(1)
                
            self.project_id = project_id
            return self.project_id
            
        except Exception as e:
            print(f"Error getting project ID: {e}")
            sys.exit(1)
    
    def get_service_details(self):
        """Get service details from a recent deployment."""
        project_id = self.get_project_id()
        if not project_id:
            print("Failed to determine project ID.")
            return
        
        try:
            if not self.service:
                # Get list of services if not specified
                result = self.run_gcloud_command([
                    "run", "services", "list", 
                    f"--project={project_id}", 
                    "--format=json"
                ])
                
                try:
                    services = json.loads(result.stdout)
                except json.JSONDecodeError:
                    print(f"Error parsing service list output: {result.stdout}")
                    return
                    
                if not services:
                    print("No Cloud Run services found in the project.")
                    return
                
                # Use the first service as default
                self.service = services[0]["metadata"]["name"]
                self.region = re.search(r'locations/([^/]+)', services[0]["metadata"]["name"]).group(1)
                
                print(f"Using service: {self.service} in region: {self.region}")
        
        except Exception as e:
            print(f"Error fetching service details: {e}")
            return
    
    def fetch_logs(self, time_period="1h", limit=100, include_request=False, severity=None, 
                   output_format="text", follow=False, tail=None):
        """Fetch logs for the specified Cloud Run service."""
        project_id = self.get_project_id()
        if not project_id:
            return
        
        if not self.service:
            self.get_service_details()
            if not self.service:
                return
        
        # Build the log filter
        filter_parts = [
            f'resource.type="cloud_run_revision"',
            f'resource.labels.service_name="{self.service}"'
        ]
        
        if self.region:
            filter_parts.append(f'resource.labels.location="{self.region}"')
        
        if severity:
            filter_parts.append(f'severity="{severity}"')
        
        if include_request:
            filter_parts.append('jsonPayload.httpRequest:*')
        
        log_filter = ' AND '.join(filter_parts)
        
        # Build the gcloud command
        cmd = [
            "logging", "read",
            f"{log_filter}",
            f"--project={project_id}",
            f"--limit={limit}"
        ]
        
        if time_period:
            cmd.append(f"--freshness={time_period}")
        
        if follow:
            cmd.append("--follow")
        
        if tail:
            cmd.append(f"--tail={tail}")
        
        if output_format == "json":
            cmd.append("--format=json")
        
        # Generate output filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(
            self.output_dir, 
            f"{self.service}_logs_{timestamp}.{output_format}"
        )
        
        print(f"Fetching logs for {self.service}...")
        print(f"Command: {self.gcloud_path} {' '.join(cmd)}")
        
        try:
            # Execute command
            if follow:
                # For streaming logs, we need to use Popen
                with open(output_file, 'w') as f:
                    cmd_full = [self.gcloud_path] + cmd
                    process = subprocess.Popen(
                        cmd_full,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        universal_newlines=True
                    )
                    
                    print("Streaming logs (Ctrl+C to stop)...")
                    try:
                        for line in process.stdout:
                            print(line, end='')
                            f.write(line)
                            f.flush()
                    except KeyboardInterrupt:
                        process.terminate()
                        print("\nLog streaming stopped.")
            else:
                # For regular log fetch
                with open(output_file, 'w') as f:
                    result = self.run_gcloud_command(cmd, check=False)
                    if result.returncode != 0:
                        print(f"Error fetching logs: {result.stderr}")
                        return
                    f.write(result.stdout)
                
                print(f"Logs saved to: {output_file}")
                
                # Display logs on screen if needed
                try:
                    with open(output_file, 'r') as f:
                        log_content = f.read()
                        if log_content.strip():
                            print("\n--- Log Preview ---")
                            # Print first few lines as preview
                            preview_lines = 500
                            lines = log_content.split('\n')
                            for i, line in enumerate(lines):
                                if i >= preview_lines:
                                    print(f"... {len(lines) - preview_lines} more lines ...")
                                    break
                                print(line)
                        else:
                            print("No logs found for the specified criteria.")
                except Exception as e:
                    print(f"Error displaying log preview: {e}")
            
            return output_file
                
        except Exception as e:
            print(f"Error executing command: {e}")
            return None
    
    def watch_deployment(self, service=None, region=None, max_wait=300, poll_interval=10):
        """Watch logs after a deployment."""
        if service:
            self.service = service
        if region:
            self.region = region
            
        if not self.service:
            self.get_service_details()
            if not self.service:
                return
        
        print(f"Watching for logs from {self.service} deployment...")
        
        # Get the current timestamp
        start_time = datetime.datetime.now()
        end_time = start_time + datetime.timedelta(seconds=max_wait)
        
        while datetime.datetime.now() < end_time:
            # Calculate time since we started watching
            elapsed = (datetime.datetime.now() - start_time).total_seconds()
            print(f"Checking for logs ({elapsed:.0f}s elapsed)...")
            
            # Fetch recent logs (just since we started watching)
            time_period = f"{int(elapsed) + 60}s"  # Add a buffer
            
            self.fetch_logs(time_period=time_period, limit=50)
            
            # Wait before polling again
            time.sleep(poll_interval)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Google Cloud Run Log Fetcher')
    
    # Service identification
    parser.add_argument('--project', help='Google Cloud project ID')
    parser.add_argument('--service', help='Cloud Run service name')
    parser.add_argument('--region', help='Cloud Run service region')
    
    # Log filtering options
    parser.add_argument('--time', default='1h', help='Time period for logs (e.g., 1h, 30m, 2d)')
    parser.add_argument('--limit', type=int, default=100, help='Maximum number of log entries')
    parser.add_argument('--severity', choices=['DEBUG', 'INFO', 'NOTICE', 'WARNING', 'ERROR', 'CRITICAL', 'ALERT', 'EMERGENCY'], 
                        help='Filter by severity level')
    parser.add_argument('--include-requests', action='store_true', help='Include HTTP request details')
    
    # Output options
    parser.add_argument('--output-dir', help='Directory to save log files')
    parser.add_argument('--format', choices=['text', 'json'], default='text', help='Output format')
    
    # Streaming options
    parser.add_argument('--follow', action='store_true', help='Stream logs in real-time')
    parser.add_argument('--tail', type=int, help='Show only the most recent N log entries')
    
    # Watch deployment mode
    parser.add_argument('--watch-deployment', action='store_true', 
                        help='Watch logs after deployment (polls periodically)')
    parser.add_argument('--max-wait', type=int, default=300, 
                        help='Maximum time to watch for logs (seconds)')
    parser.add_argument('--poll-interval', type=int, default=10,
                        help='Interval between log checks (seconds)')
    
    # gcloud path
    parser.add_argument('--gcloud-path', help='Path to gcloud executable')
    
    return parser.parse_args()


def main():
    args = parse_arguments()
    
    log_fetcher = CloudRunLogFetcher(
        project_id=args.project,
        service=args.service,
        region=args.region,
        output_dir=args.output_dir,
        gcloud_path=args.gcloud_path
    )
    
    if args.watch_deployment:
        log_fetcher.watch_deployment(
            max_wait=args.max_wait,
            poll_interval=args.poll_interval
        )
    else:
        log_fetcher.fetch_logs(
            time_period=args.time,
            limit=args.limit,
            include_request=args.include_requests,
            severity=args.severity,
            output_format=args.format,
            follow=args.follow,
            tail=args.tail
        )


if __name__ == "__main__":
    main()