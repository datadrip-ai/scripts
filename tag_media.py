# todo: requirements, settings ini file, sanitizing filenames

import os
import logging
import subprocess
import csv
from pathlib import Path
import ffmpeg
import shutil
import time
from colorama import init, Fore, Style
from tqdm import tqdm
from dotenv import load_dotenv
from PIL import Image
from transformers import pipeline
import pandas as pd
import hashlib

# Initialize colorama for colored console output
init(autoreset=True)

# Load .env file
load_dotenv()

# Configuration
VIDEO_DIR = os.getenv("VIDEO_DIR_PY", "../public/videos")
THUMBS_DIR = os.getenv("THUMBS_DIR", "../public/thumbnails")
TAGS_CSV = os.getenv("TAGS_CSV", "../public/tags.csv")
INPUT_TAGS = os.getenv("INPUT_TAGS", "../public/selected_tags.csv")
EXCLUSIONS = os.getenv("EXCLUSIONS", "../public/exclusions.csv")
THUMBNAIL_URL_PREFIX = os.getenv("THUMBNAIL_URL_PREFIX", "/thumbnails")
DEFAULT_CANDIDATE_TAGS = [
    "cat", "dog", "car", "tree", "sky", "building", "person", "landscape", "night", "day",
    "beach", "forest", "city", "food", "animal", "water", "mountain", "road", "cloud", "sun"
]

# Custom logging level for success
logging.SUCCESS = 25
logging.addLevelName(logging.SUCCESS, "SUCCESS")

# Custom logging formatter for colored console output
class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.CYAN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'SUCCESS': Fore.GREEN,
    }

    def format(self, record):
        log_message = super().format(record)
        return f"{self.COLORS.get(record.levelname, Fore.CYAN)}{log_message}{Style.RESET_ALL}"

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler('media_processing.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(ColoredFormatter(
    '%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))

logger.addHandler(file_handler)
logger.addHandler(console_handler)

def get_path(*segments: str) -> Path:
    """Generate a path relative to the project, handling .env variables."""
    try:
        base = Path(os.getenv(segments[0], segments[0]) if segments[0] in os.environ else segments[0])
        return base.joinpath(*segments[1:]).resolve()
    except Exception as e:
        logger.error(f"Failed to resolve path for {segments}: {str(e)}")
        raise

def get_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as e:
        logger.error(f"Failed to hash {file_path}: {str(e)}")
        return ""

def get_video_duration(file_path: str) -> float:
    """Get video duration using ffprobe."""
    try:
        probe = ffmpeg.probe(file_path)
        duration = float(probe["format"]["duration"])
        logger.info(f"Duration for {file_path}: {duration:.2f}s")
        return duration
    except ffmpeg.Error as e:
        logger.error(f"FFprobe error for {file_path}: {e.stderr.decode()}")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error getting duration for {file_path}: {str(e)}")
        return 0

def generate_jpeg(file_path: str, video_id: str, duration: float) -> str:
    """Generate a JPEG thumbnail at 10% of duration, 480x270."""
    preview_dir = get_path(THUMBS_DIR, "preview")
    preview_dir.mkdir(parents=True, exist_ok=True)
    jpeg_path = preview_dir / f"{video_id}_thumb.jpg"

    timestamp = min(max(duration * 0.1, 0), duration)
    try:
        subprocess.run(
            [
                "ffmpeg", "-i", file_path, "-ss", str(timestamp), "-vframes", "1",
                "-vf", "scale=480:270:force_original_aspect_ratio=decrease,pad=480:270:(ow-iw)/2:(oh-ih)/2",
                "-q:v", "6", str(jpeg_path), "-y"
            ],
            check=True, capture_output=True, text=True
        )
        jpeg_size = jpeg_path.stat().st_size / 1024
        logger.log(logging.SUCCESS, f"Generated JPEG for {video_id}: {jpeg_path} ({jpeg_size:.2f} KB)")
        return f"{THUMBNAIL_URL_PREFIX}/preview/{video_id}_thumb.jpg"
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg JPEG error for {video_id}: {e.stderr}")
        return ""
    except Exception as e:
        logger.error(f"Unexpected error generating JPEG for {video_id}: {str(e)}")
        return ""

def generate_gif(file_path: str, video_id: str, duration: float) -> str:
    """Generate a 2-second GIF at 10% of duration, 640x360, 10 fps."""
    preview_dir = get_path(THUMBS_DIR, "preview")
    preview_dir.mkdir(parents=True, exist_ok=True)
    gif_path = preview_dir / f"{video_id}.gif"

    start_time = min(max(duration * 0.5, 0), duration)
    try:
        subprocess.run(
            [
                "ffmpeg", "-i", file_path, "-ss", str(start_time), "-t", "2",
                "-vf", "fps=10,scale=480:270:force_original_aspect_ratio=decrease,pad=480:270:(ow-iw)/2:(oh-ih)/2",
                "-c:v", "gif", "-crf", "28", str(gif_path), "-y"
            ],
            check=True, capture_output=True, text=True
        )
        gif_size = gif_path.stat().st_size / 1024
        logger.log(logging.SUCCESS, f"Generated GIF for {video_id}: {gif_path} ({gif_size:.2f} KB)")
        return f"{THUMBNAIL_URL_PREFIX}/preview/{video_id}.gif"
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg GIF error for {video_id}: {e.stderr}")
        return ""
    except Exception as e:
        logger.error(f"Unexpected error generating GIF for {video_id}: {str(e)}")
        return ""

def load_candidate_tags() -> list:
    """Load candidate tags from INPUT_TAGS, exclude tags from EXCLUSIONS, fallback to DEFAULT_CANDIDATE_TAGS."""
    logger.info(f"Loading candidate tags from {INPUT_TAGS}...")
    try:
        df = pd.read_csv(INPUT_TAGS, dtype={'tag_id': str, 'name': str, 'category': str, 'count': int})
        if not all(col in df.columns for col in ['tag_id', 'name', 'category', 'count']):
            logger.error(f"Invalid CSV format in {INPUT_TAGS}: Missing required columns")
            return DEFAULT_CANDIDATE_TAGS
        if df['tag_id'].duplicated().any():
            logger.warning(f"Duplicate tag_ids found in {INPUT_TAGS}")
        if df['name'].isna().any() or (df['name'] == '').any():
            logger.warning(f"Empty or missing tag names in {INPUT_TAGS}")
        valid_tags = df[df['name'].notna() & (df['name'] != '') & (df['count'] > 100)]
        tags = valid_tags.sort_values('count', ascending=False)['name'].tolist()

        excluded_tags = set()
        try:
            exclusions_df = pd.read_csv(EXCLUSIONS)
            if 'name' in exclusions_df.columns:
                excluded_tags = set(exclusions_df['name'].dropna().str.lower())
                logger.info(f"Loaded {len(excluded_tags)} excluded tags from {EXCLUSIONS}")
            else:
                logger.warning(f"No 'name' column found in {EXCLUSIONS}, skipping exclusions")
        except FileNotFoundError:
            logger.warning(f"{EXCLUSIONS} not found, skipping exclusions")
        except pd.errors.ParserError:
            logger.warning(f"Failed to parse {EXCLUSIONS}: Invalid CSV format, skipping exclusions")
        except Exception as e:
            logger.error(f"Unexpected error loading {EXCLUSIONS}: {str(e)}")
            logger.warning("Skipping exclusions due to error")

        filtered_tags = [tag for tag in tags if tag.lower() not in excluded_tags]
        if not filtered_tags:
            logger.warning(f"No valid tags remain after filtering exclusions from {INPUT_TAGS}")
            return DEFAULT_CANDIDATE_TAGS
        logger.log(logging.SUCCESS, f"Loaded {len(filtered_tags)} candidate tags from {INPUT_TAGS}")
        return filtered_tags[:50]
    except FileNotFoundError:
        logger.error(f"{INPUT_TAGS} not found")
        return DEFAULT_CANDIDATE_TAGS
    except pd.errors.ParserError:
        logger.error(f"Failed to parse {INPUT_TAGS}: Invalid CSV format")
        return DEFAULT_CANDIDATE_TAGS
    except Exception as e:
        logger.error(f"Unexpected error loading {INPUT_TAGS}: {str(e)}")
        return DEFAULT_CANDIDATE_TAGS

def tag_image(image_path: str, tagger, candidate_tags: list) -> list:
    """Tag image using CLIP pipeline, return top 20 tags with confidence scores."""
    logger.debug(f"Tagging image: {image_path}")
    try:
        image = Image.open(image_path).convert("RGB")
        results = tagger(image, candidate_labels=candidate_tags)
        tag_data = sorted(results, key=lambda x: x['score'], reverse=True)[:20]
        tags = [item['label'] for item in tag_data]
        logger.log(logging.SUCCESS, f"Tags for {image_path}: {', '.join(f'{item['label']} ({item['score']:.2f})' for item in tag_data)}")
        return tags
    except Exception as e:
        logger.error(f"Error tagging {image_path}: {str(e)}")
        return []

def load_existing_tags() -> list:
    """Load existing tags.csv if it exists."""
    logger.debug(f"Checking for existing {TAGS_CSV}...")
    tags_data = []
    if Path(TAGS_CSV).exists():
        try:
            with open(TAGS_CSV, "r", newline="") as f:
                reader = csv.DictReader(f)
                tags_data = list(reader)
            logger.info(f"Loaded {len(tags_data)} existing tags from {TAGS_CSV}")
        except Exception as e:
            logger.error(f"Failed to load {TAGS_CSV}: {str(e)}")
    return tags_data

def clean_orphaned_tags(tags_data: list, video_files: list) -> list:
    """Remove tags for videos no longer in VIDEO_DIR."""
    logger.info("Cleaning orphaned tags...")
    video_ids = {Path(v).stem for v in video_files}
    valid_tags = []
    removed_count = 0
    for entry in tags_data:
        media_id = entry["media_id"]
        if media_id in video_ids:
            valid_tags.append(entry)
        else:
            logger.warning(f"Removed orphaned tag for video:{media_id}")
            removed_count += 1
    logger.log(logging.SUCCESS, f"Cleaned {removed_count} orphaned tags, {len(valid_tags)} tags retained")
    return valid_tags

def clean_thumbnails(video_files: list):
    """Remove orphaned thumbnails and GIFs in THUMBS_DIR/preview."""
    preview_dir = get_path(THUMBS_DIR, "preview")
    preview_dir.mkdir(parents=True, exist_ok=True)
    video_ids = {Path(v).stem for v in video_files}
    removed_count = 0

    logger.info("Cleaning orphaned thumbnails and GIFs...")
    try:
        for file in preview_dir.glob("*"):
            file_id = file.stem if file.suffix == ".gif" else file.stem.replace("_thumb", "")
            if file_id not in video_ids:
                try:
                    file.unlink()
                    logger.log(logging.SUCCESS, f"Removed orphaned file: {file}")
                    removed_count += 1
                except OSError as e:
                    logger.error(f"Failed to remove {file}: {str(e)}")
        logger.log(logging.SUCCESS, f"Cleaned {removed_count} orphaned files")
    except Exception as e:
        logger.error(f"Unexpected error during thumbnail cleanup: {str(e)}")

def get_video_files() -> list:
    """Scan VIDEO_DIR recursively for .mp4 and .webm files."""
    video_dir = get_path(VIDEO_DIR)
    video_files = []
    try:
        for file in video_dir.rglob("*"):
            if file.suffix.lower() in [".mp4", ".webm"]:
                video_files.append(str(file.relative_to(video_dir)))
        logger.info(f"Found {len(video_files)} videos")
        return sorted(video_files)
    except OSError as e:
        logger.error(f"Failed to scan {VIDEO_DIR}: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error scanning {VIDEO_DIR}: {str(e)}")
        return []

def prompt_user() -> tuple[bool, bool, bool]:
    """Prompt user for thumbnail/GIF generation, tagging, and cache clearing."""
    logger.info(f"{Fore.MAGENTA}Starting media processing configuration...")
    
    while True:
        response = input(f"{Fore.CYAN}Generate thumbnails and GIFs for videos? (y/n): {Style.RESET_ALL}").strip().lower()
        if response in ['y', 'n']:
            generate_thumbs = response == 'y'
            break
        logger.warning("Invalid input, please enter 'y' or 'n'")

    while True:
        response = input(f"{Fore.CYAN}Generate tags for thumbnails? (y/n): {Style.RESET_ALL}").strip().lower()
        if response in ['y', 'n']:
            generate_tags = response == 'y'
            break
        logger.warning("Invalid input, please enter 'y' or 'n'")

    clear_cache = False
    if generate_thumbs or generate_tags:
        while True:
            response = input(f"{Fore.YELLOW}Clear thumbnail, GIF, and tag cache? This will back up existing files. (y/n): {Style.RESET_ALL}").strip().lower()
            if response in ['y', 'n']:
                clear_cache = response == 'y'
                break
            logger.warning("Invalid input, please enter 'y' or 'n'")

    logger.info(f"Configuration: Thumbnails/GIFs={generate_thumbs}, Tags={generate_tags}, Clear Cache={clear_cache}")
    return generate_thumbs, generate_tags, clear_cache

def process_media():
    """Generate thumbnails, GIFs, and tags for videos, with user prompts and duplication checks."""
    start_time = time.time()
    logger.info(f"{Fore.MAGENTA}Starting media processing...")

    # Get user preferences
    generate_thumbs, generate_tags, clear_cache = prompt_user()

    # Get video files
    video_files = get_video_files()
    total_videos = len(video_files)
    success_count = 0
    tags_data = load_existing_tags() if generate_tags else []
    existing_tag_ids = {entry["media_id"] for entry in tags_data}

    # Handle cache clearing
    if clear_cache:
        logger.info("Initiating cache clearing...")
        backup_dir = Path("backup") / f"backup_{time.strftime('%Y%m%d_%H%M%S')}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        preview_dir = get_path(THUMBS_DIR, "preview")
        if preview_dir.exists():
            try:
                shutil.copytree(preview_dir, backup_dir / "thumbnails")
                logger.log(logging.SUCCESS, f"Backed up thumbnails and GIFs to {backup_dir / 'thumbnails'}")
            except Exception as e:
                logger.error(f"Failed to back up thumbnails: {str(e)}")
                return

        if Path(TAGS_CSV).exists():
            try:
                shutil.copy(TAGS_CSV, backup_dir / "tags.csv")
                logger.log(logging.SUCCESS, f"Backed up {TAGS_CSV} to {backup_dir / 'tags.csv'}")
            except Exception as e:
                logger.error(f"Failed to back up {TAGS_CSV}: {str(e)}")
                return

        try:
            if preview_dir.exists():
                shutil.rmtree(preview_dir)
                logger.log(logging.SUCCESS, f"Cleared thumbnail and GIF cache: {preview_dir}")
            if Path(TAGS_CSV).exists():
                Path(TAGS_CSV).unlink()
                logger.log(logging.SUCCESS, f"Cleared tags cache: {TAGS_CSV}")
            preview_dir.mkdir(parents=True, exist_ok=True)
            tags_data = []
            existing_tag_ids = set()
        except Exception as e:
            logger.error(f"Failed to clear cache: {str(e)}")
            return

    # Load CLIP pipeline for tagging
    tagger = None
    if generate_tags:
        logger.debug("Loading CLIP pipeline...")
        try:
            tagger = pipeline("zero-shot-image-classification", model="openai/clip-vit-base-patch32")
            logger.log(logging.SUCCESS, "CLIP pipeline loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load CLIP pipeline: {str(e)}")
            logger.warning("Continuing with empty tags due to model failure")

    # Load candidate tags
    candidate_tags = load_candidate_tags() if generate_tags else []

    # Clean orphaned thumbnails and GIFs (if not cleared)
    if generate_thumbs and not clear_cache:
        clean_thumbnails(video_files)

    # Process videos
    for i, rel_path in enumerate(tqdm(video_files, desc="Processing videos", unit="video"), 1):
        file_path = get_path(VIDEO_DIR, rel_path)
        video_id = Path(rel_path).stem
        logger.info(f"{Fore.MAGENTA}Processing video {i}/{total_videos}: {rel_path}")

        try:
            duration = get_video_duration(str(file_path))
            if duration < 5:
                logger.warning(f"Skipping {rel_path}: Duration {duration:.2f}s < 5s")
                continue

            # Generate thumbnail and GIF if needed
            jpeg_url = ""
            gif_url = ""
            jpeg_path = get_path(THUMBS_DIR, "preview", f"{video_id}_thumb.jpg")
            gif_path = get_path(THUMBS_DIR, "preview", f"{video_id}.gif")
            if generate_thumbs:
                if not jpeg_path.exists():
                    jpeg_url = generate_jpeg(str(file_path), video_id, duration)
                    if not jpeg_url:
                        logger.warning(f"Failed to generate JPEG for {rel_path}")
                        continue
                else:
                    jpeg_url = f"{THUMBNAIL_URL_PREFIX}/preview/{video_id}_thumb.jpg"
                    logger.info(f"JPEG exists: {jpeg_path} ({jpeg_path.stat().st_size / 1024:.2f} KB)")

                if not gif_path.exists():
                    gif_url = generate_gif(str(file_path), video_id, duration)
                    if not gif_url:
                        logger.warning(f"Failed to generate GIF for {rel_path}")
                        continue
                else:
                    gif_url = f"{THUMBNAIL_URL_PREFIX}/preview/{video_id}.gif"
                    logger.info(f"GIF exists: {gif_path} ({gif_path.stat().st_size / 1024:.2f} KB)")
            elif not (jpeg_path.exists() and gif_path.exists()):
                logger.warning(f"Thumbnail or GIF missing for {rel_path}, but generation disabled")
                continue

            # Generate tags if needed
            if generate_tags and video_id not in existing_tag_ids:
                tags = []
                if tagger:
                    tags = tag_image(str(jpeg_path), tagger, candidate_tags)
                    if not tags:
                        logger.warning(f"No tags generated for {rel_path}")
                else:
                    logger.warning(f"Skipping tagging for {rel_path} due to model failure")
                tags_data.append({
                    "media_id": video_id,
                    "media_type": "video",
                    **{f"tag{i}": tag for i, tag in enumerate(tags, 1)}
                })
                success_count += 1
            elif video_id in existing_tag_ids:
                logger.info(f"Tags already exist for {video_id}, skipping")

        except Exception as e:
            logger.error(f"Unexpected error processing {rel_path}: {str(e)}")

    # Clean orphaned tags
    if generate_tags:
        tags_data = clean_orphaned_tags(tags_data, video_files)

    # Write tags.csv
    if generate_tags and tags_data:
        logger.debug("Writing tags.csv...")
        try:
            with open(TAGS_CSV, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["media_id", "media_type"] + [f"tag{i}" for i in range(1, 21)])
                writer.writeheader()
                writer.writerows(tags_data)
            logger.log(logging.SUCCESS, f"Generated {TAGS_CSV}: {len(tags_data)} videos tagged")
        except Exception as e:
            logger.error(f"Failed to write {TAGS_CSV}: {str(e)}")

    elapsed_time = time.time() - start_time
    logger.info(
        f"{Fore.MAGENTA}Media processing complete: {success_count}/{total_videos} videos processed "
        f"in {elapsed_time:.2f} seconds"
    )

if __name__ == "__main__":
    process_media()