import os
import time
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory, url_for
from ltx_core.loader import LTXV_LORA_COMFY_RENAMING_MAP, LoraPathStrengthAndSDOps
from ltx_pipelines.ti2vid_two_stages import TI2VidTwoStagesPipeline

app = Flask(__name__)
OUTPUT_DIR = Path(os.environ.get("LTX_OUTPUT_DIR", "/outputs"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

_PIPELINE: TI2VidTwoStagesPipeline | None = None


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _resolution_to_size(label: str) -> tuple[int, int]:
    match label:
        case "1080p":
            return 1920, 1080
        case "720p":
            return 1280, 720
        case "540p":
            return 960, 540
        case _:
            return 1280, 720


def _frames_for_duration(duration_seconds: int, fps: int) -> int:
    base_frames = duration_seconds * fps + 1
    remainder = (base_frames - 1) % 8
    if remainder == 0:
        return base_frames
    return base_frames + (8 - remainder)


def _get_pipeline() -> TI2VidTwoStagesPipeline:
    global _PIPELINE
    if _PIPELINE is None:
        checkpoint_path = _require_env("LTX_CHECKPOINT_PATH")
        gemma_root = _require_env("LTX_GEMMA_ROOT")
        upsampler_path = _require_env("LTX_UPSAMPLER_PATH")
        lora_path = os.environ.get("LTX_DISTILLED_LORA_PATH")
        lora_strength = float(os.environ.get("LTX_DISTILLED_LORA_STRENGTH", "0.6"))
        distilled_lora = []
        if lora_path:
            distilled_lora.append(
                LoraPathStrengthAndSDOps(
                    lora_path,
                    lora_strength,
                    LTXV_LORA_COMFY_RENAMING_MAP,
                )
            )
        _PIPELINE = TI2VidTwoStagesPipeline(
            checkpoint_path=checkpoint_path,
            distilled_lora=distilled_lora,
            spatial_upsampler_path=upsampler_path,
            gemma_root=gemma_root,
            loras=[],
        )
    return _PIPELINE


@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.post("/generate")
def generate() -> tuple[dict, int] | tuple[str, int]:
    payload = request.get_json(silent=True) or {}
    prompt = (payload.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"error": "Prompt is required."}), 400

    duration_seconds = int(payload.get("duration_seconds", 6))
    fps = int(payload.get("fps", 25))
    resolution = payload.get("resolution", "1080p")
    width, height = _resolution_to_size(resolution)
    num_frames = _frames_for_duration(duration_seconds, fps)

    output_name = f"ltx_{int(time.time())}.mp4"
    output_path = OUTPUT_DIR / output_name

    try:
        pipeline = _get_pipeline()
        pipeline(
            prompt=prompt,
            output_path=str(output_path),
            seed=int(payload.get("seed", 42)),
            height=height,
            width=width,
            num_frames=num_frames,
            frame_rate=float(fps),
            num_inference_steps=int(payload.get("num_inference_steps", 40)),
            cfg_guidance_scale=float(payload.get("cfg_guidance_scale", 3.0)),
        )
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 500

    return jsonify({"output_url": url_for("outputs", filename=output_name)}), 200


@app.route("/outputs/<path:filename>")
def outputs(filename: str):
    return send_from_directory(OUTPUT_DIR, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
