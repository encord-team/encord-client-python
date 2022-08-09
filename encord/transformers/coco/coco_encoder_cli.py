import argparse
import json
from pathlib import Path
from typing import List

from encord.objects.ontology_structure import OntologyStructure
from encord.transformers.coco.coco_encoder import CocoEncoder


def get_labels(config: dict) -> List[dict]:
    if "labels" not in config:
        return []
    else:
        return config["labels"]


def get_ontology(config: dict) -> OntologyStructure:
    if "ontology" not in config:
        return OntologyStructure()

    ontology_dict = config["ontology"]
    return OntologyStructure.from_dict(ontology_dict)


def coco_run_from_config(config: dict) -> dict:
    labels = get_labels(config)
    ontology = get_ontology(config)
    # Get configuration arguments
    download_files = config.get("download_files", False)
    download_file_path = Path(config.get("download_file_path", "."))
    include_videos = config.get("include_videos", False)
    include_unannotated_videos = config.get("include_unannotated_videos", False)

    return CocoEncoder(labels, ontology).encode(
        download_files, download_file_path, include_videos, include_unannotated_videos
    )


def coco_encoder_cli():
    print("Starting up the COCO encoder CLI...")
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-c", "--config", help="The config file. Every CocoEncoder argument will be taken from there", type=Path
    )
    parser.add_argument("--results", help="Path to where the results should be stored", type=Path)
    args = parser.parse_args()
    file_path = args.config
    with file_path.open() as f:
        config = json.load(f)

    res = coco_run_from_config(config)
    with args.results.open("w") as results_path:
        json.dump(res, results_path)


def coco_encoder_cli_sdk():
    print("Starting up the COCO encoder CLI...")
    parser = argparse.ArgumentParser()

    parser.add_argument("-l", "--labels", help="Supply a comma separated list of label hashes.", type=str)
    parser.add_argument("-o", "--ontology", help="Supply the ontology hash", type=str)
    parser.add_argument(
        "-d",
        "--download-files",
        dest="download_files",
        help="Specify whether to download files. Default False",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "-p",
        "--download-file-path",
        dest="download_file_path",
        help='Path to the root directory of the files. Default Path(".")',
        default=Path("."),
        type=Path,
    )
    parser.add_argument(
        "-v",
        "--include-videos",
        dest="include_videos",
        help="Whether to include videos. Default False",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--include-unannotated-videos",
        dest="include_unannotated_videos",
        help="Whether to include videos that are not annotated",
        default=False,
        action="store_true",
    )
    args = parser.parse_args()
    label_hashes = args.labels.split(",")
    print(f"labels = {label_hashes}")
    print(f"ontology = {args.ontology}")
    print(f"download_files = {args.download_files}")
    print(f"download_file_path = {args.download_file_path}")
    print(f"include_videos = {args.include_videos}")
    print(f"include_unannotated_videos = {args.include_unannotated_videos}")
