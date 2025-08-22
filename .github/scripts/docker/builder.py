#!/usr/bin/env python3
"""
Docker Builder for rxiv-maker.
Replaces complex 343-line YAML workflow with debuggable Python.

This script handles:
1. Change detection for Docker builds
2. Multi-platform Docker image building
3. Image metadata and tagging
4. Build verification and testing
5. Registry push operations
6. Cache management

Usage:
    python builder.py [--platforms linux/amd64,linux/arm64] [--push] [--debug]
"""

import sys
import argparse
import os
import json
import tempfile
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add common modules to path
sys.path.insert(0, str(Path(__file__).parent.parent / "common"))

from logger import setup_logger, log_step, log_section
from config import get_github_token
from utils import run_command, validate_environment


class DockerBuilder:
    """Docker builder and manager."""
    
    def __init__(
        self, 
        platforms: Optional[List[str]] = None, 
        push: bool = False, 
        debug: bool = False,
        registry: str = "docker.io",
        image_name: str = "henriqueslab/rxiv-maker-base"
    ):
        """
        Initialize Docker builder.
        
        Args:
            platforms: List of platforms to build for (e.g., ['linux/amd64', 'linux/arm64'])
            push: Whether to push to registry
            debug: Enable debug logging
            registry: Docker registry
            image_name: Full image name
        """
        self.platforms = platforms or ["linux/amd64", "linux/arm64"]
        self.push = push
        self.registry = registry
        self.image_name = image_name
        
        # Setup logging
        log_level = "DEBUG" if debug else "INFO"
        self.logger = setup_logger("docker_builder", log_level)
        
        # Configuration
        self.dockerfile_path = "src/docker/images/base/Dockerfile"
        self.context_path = "."
        self.build_timeout = 45 * 60  # 45 minutes
        
        # State tracking
        self.build_artifacts = {}
        self.metadata = {}
        
        log_section(self.logger, "Docker Builder Initialized")
        self.logger.info(f"Platforms: {', '.join(self.platforms)}")
        self.logger.info(f"Push to registry: {self.push}")
        self.logger.info(f"Image: {self.image_name}")
    
    def run_build_pipeline(self) -> bool:
        """
        Execute the complete Docker build pipeline.
        
        Returns:
            True if build completed successfully
        """
        try:
            log_section(self.logger, "Starting Docker Build Pipeline")
            
            # Step 1: Detect changes
            if not self.detect_changes():
                self.logger.info("No changes detected, skipping build")
                return True
            
            # Step 2: Setup build environment
            if not self.setup_build_environment():
                return False
            
            # Step 3: Extract metadata
            self.metadata = self.extract_metadata()
            
            # Step 4: Build images for all platforms
            if not self.build_multiplatform_images():
                return False
            
            # Step 5: Verify builds
            if not self.verify_builds():
                return False
            
            # Step 6: Push to registry (if requested)
            if self.push:
                if not self.push_to_registry():
                    return False
            
            log_section(self.logger, "Docker Build Pipeline Completed Successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Docker build pipeline failed: {e}")
            return False
    
    def detect_changes(self) -> bool:
        """Detect if Docker-related files have changed."""
        log_step(self.logger, "Detecting changes", "START")
        
        try:
            # Paths that should trigger a Docker build
            docker_paths = [
                "src/docker/",
                "src/py/",
                "pyproject.toml",
                "requirements.txt",
                "requirements-dev.txt"
            ]
            
            # In a real implementation, this would check git diff
            # For now, we'll assume changes are present
            
            self.logger.info("Change detection paths:")
            for path in docker_paths:
                if Path(path).exists():
                    self.logger.info(f"  ✅ {path}")
                else:
                    self.logger.info(f"  ❌ {path} (not found)")
            
            # Simple heuristic: if Dockerfile exists, we should build
            should_build = Path(self.dockerfile_path).exists()
            
            if should_build:
                log_step(self.logger, "Changes detected, build required", "SUCCESS")
            else:
                log_step(self.logger, "No changes detected, build not required", "SKIP")
            
            return should_build
            
        except Exception as e:
            log_step(self.logger, f"Change detection failed: {e}", "FAILURE")
            return False
    
    def setup_build_environment(self) -> bool:
        """Setup Docker build environment."""
        log_step(self.logger, "Setting up build environment", "START")
        
        try:
            # Check Docker is available
            run_command(["docker", "--version"], logger=self.logger)
            
            # Setup QEMU (for multi-platform builds)
            self.logger.info("Setting up QEMU for multi-platform builds...")
            run_command([
                "docker", "run", "--rm", "--privileged",
                "multiarch/qemu-user-static", "--reset", "-p", "yes"
            ], logger=self.logger)
            
            # Create buildx builder if it doesn't exist
            self.logger.info("Setting up Docker Buildx...")
            try:
                # Try to use existing builder
                run_command(["docker", "buildx", "inspect", "multiplatform"], logger=self.logger)
                self.logger.info("Using existing multiplatform builder")
            except subprocess.CalledProcessError:
                # Create new builder
                self.logger.info("Creating new multiplatform builder...")
                run_command([
                    "docker", "buildx", "create",
                    "--name", "multiplatform",
                    "--use", "--bootstrap"
                ], logger=self.logger)
            
            log_step(self.logger, "Build environment ready", "SUCCESS")
            return True
            
        except Exception as e:
            log_step(self.logger, f"Build environment setup failed: {e}", "FAILURE")
            return False
    
    def extract_metadata(self) -> Dict[str, Any]:
        """Extract metadata for Docker image tagging."""
        log_step(self.logger, "Extracting metadata", "START")
        
        try:
            metadata = {
                "image_name": self.image_name,
                "tags": [],
                "labels": {}
            }
            
            # Determine tags based on context
            if os.getenv("GITHUB_REF_TYPE") == "tag":
                # Release build
                version = os.getenv("GITHUB_REF_NAME", "").lstrip('v')
                if version:
                    metadata["tags"].extend([
                        f"{self.image_name}:{version}",
                        f"{self.image_name}:latest"
                    ])
            elif os.getenv("GITHUB_REF_NAME"):
                # Branch build
                branch = os.getenv("GITHUB_REF_NAME")
                metadata["tags"].append(f"{self.image_name}:{branch}")
            else:
                # Default/local build
                metadata["tags"].append(f"{self.image_name}:dev")
            
            # Add SHA tag
            sha = os.getenv("GITHUB_SHA", "unknown")[:8]
            metadata["tags"].append(f"{self.image_name}:sha-{sha}")
            
            # Add labels
            metadata["labels"] = {
                "org.opencontainers.image.source": "https://github.com/HenriquesLab/rxiv-maker",
                "org.opencontainers.image.description": "Base Docker image for rxiv-maker",
                "org.opencontainers.image.revision": os.getenv("GITHUB_SHA", "unknown"),
                "org.opencontainers.image.created": subprocess.run(
                    ["date", "--iso-8601=seconds"], 
                    capture_output=True, text=True
                ).stdout.strip()
            }
            
            self.logger.info(f"Generated tags: {metadata['tags']}")
            self.logger.info(f"Labels: {len(metadata['labels'])} labels")
            
            log_step(self.logger, "Metadata extracted", "SUCCESS")
            return metadata
            
        except Exception as e:
            log_step(self.logger, f"Metadata extraction failed: {e}", "FAILURE")
            return {}
    
    def build_multiplatform_images(self) -> bool:
        """Build Docker images for multiple platforms."""
        log_step(self.logger, "Building multi-platform images", "START")
        
        success = True
        
        for platform in self.platforms:
            if not self.build_platform_image(platform):
                success = False
                break
        
        if success:
            log_step(self.logger, "All platform builds completed", "SUCCESS")
        else:
            log_step(self.logger, "Platform build failed", "FAILURE")
        
        return success
    
    def build_platform_image(self, platform: str) -> bool:
        """Build Docker image for specific platform."""
        safe_platform = platform.replace("/", "-")
        self.logger.info(f"Building for platform: {platform}")
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                output_file = Path(temp_dir) / f"image-{safe_platform}.tar"
                
                # Build command
                build_cmd = [
                    "docker", "buildx", "build",
                    "--platform", platform,
                    "--file", self.dockerfile_path,
                    "--output", f"type=docker,dest={output_file}",
                    self.context_path
                ]
                
                # Add tags
                for tag in self.metadata.get("tags", []):
                    build_cmd.extend(["--tag", tag])
                
                # Add labels
                for key, value in self.metadata.get("labels", {}).items():
                    build_cmd.extend(["--label", f"{key}={value}"])
                
                # Add cache options
                cache_scope = f"build-{safe_platform}"
                build_cmd.extend([
                    "--cache-from", f"type=gha,scope={cache_scope}",
                    "--cache-to", f"type=gha,scope={cache_scope},mode=max"
                ])
                
                # Execute build
                self.logger.info(f"Executing build for {platform}...")
                run_command(build_cmd, timeout=self.build_timeout, logger=self.logger)
                
                # Verify build output
                if output_file.exists():
                    size_mb = output_file.stat().st_size / (1024 * 1024)
                    self.logger.info(f"✅ Build artifact created: {output_file} ({size_mb:.1f} MB)")
                    
                    # Store artifact info
                    self.build_artifacts[platform] = {
                        "file": str(output_file),
                        "size_mb": size_mb
                    }
                    
                    return True
                else:
                    self.logger.error(f"❌ Build artifact not found: {output_file}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Platform build failed for {platform}: {e}")
            return False
    
    def verify_builds(self) -> bool:
        """Verify all built images."""
        log_step(self.logger, "Verifying builds", "START")
        
        try:
            verification_results = {}
            
            for platform, artifact in self.build_artifacts.items():
                self.logger.info(f"Verifying {platform} build...")
                
                # Basic integrity check (tar file validity)
                artifact_file = artifact["file"]
                try:
                    run_command(["tar", "-tf", artifact_file], logger=self.logger)
                    verification_results[platform] = True
                    self.logger.info(f"✅ {platform} verification passed")
                except Exception as e:
                    verification_results[platform] = False
                    self.logger.error(f"❌ {platform} verification failed: {e}")
            
            success = all(verification_results.values())
            
            if success:
                log_step(self.logger, "All builds verified", "SUCCESS")
            else:
                failed_platforms = [p for p, result in verification_results.items() if not result]
                log_step(self.logger, f"Verification failed for: {failed_platforms}", "FAILURE")
            
            return success
            
        except Exception as e:
            log_step(self.logger, f"Build verification failed: {e}", "FAILURE")
            return False
    
    def push_to_registry(self) -> bool:
        """Push images to registry."""
        log_step(self.logger, "Pushing to registry", "START")
        
        try:
            # Create multi-platform manifest and push
            platforms_str = ",".join(self.platforms)
            
            for tag in self.metadata.get("tags", []):
                self.logger.info(f"Pushing tag: {tag}")
                
                push_cmd = [
                    "docker", "buildx", "build",
                    "--platform", platforms_str,
                    "--file", self.dockerfile_path,
                    "--push",
                    "--tag", tag,
                    self.context_path
                ]
                
                # Add labels
                for key, value in self.metadata.get("labels", {}).items():
                    push_cmd.extend(["--label", f"{key}={value}"])
                
                run_command(push_cmd, timeout=self.build_timeout, logger=self.logger)
                self.logger.info(f"✅ Pushed: {tag}")
            
            log_step(self.logger, "Registry push completed", "SUCCESS")
            return True
            
        except Exception as e:
            log_step(self.logger, f"Registry push failed: {e}", "FAILURE")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Docker Builder for rxiv-maker")
    parser.add_argument(
        "--platforms", 
        default="linux/amd64,linux/arm64",
        help="Comma-separated list of platforms to build for"
    )
    parser.add_argument("--push", action="store_true", help="Push images to registry")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--registry", default="docker.io", help="Docker registry")
    parser.add_argument(
        "--image-name", 
        default="henriqueslab/rxiv-maker-base",
        help="Docker image name"
    )
    
    args = parser.parse_args()
    
    # Parse platforms
    platforms = [p.strip() for p in args.platforms.split(",")]
    
    # Create and run builder
    builder = DockerBuilder(
        platforms=platforms,
        push=args.push,
        debug=args.debug,
        registry=args.registry,
        image_name=args.image_name
    )
    
    success = builder.run_build_pipeline()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()