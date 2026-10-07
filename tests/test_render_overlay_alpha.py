import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).parents[1] / "helpers" / "render.py"
SPEC = importlib.util.spec_from_file_location("video_use_render", MODULE_PATH)
assert SPEC and SPEC.loader
render = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(render)


class OverlayInputArgsTests(unittest.TestCase):
    def test_webm_forces_libvpx_decoder_to_keep_alpha(self):
        for name in ("clip.webm", "CLIP.WEBM"):
            with self.subTest(name=name):
                self.assertEqual(
                    render.overlay_input_args(Path("/tmp") / name),
                    ["-c:v", "libvpx-vp9", "-i", str(Path("/tmp") / name)],
                )

    def test_other_containers_use_a_plain_input(self):
        for name in ("clip.mp4", "clip.mov", "clip.mkv"):
            with self.subTest(name=name):
                self.assertEqual(
                    render.overlay_input_args(Path("/tmp") / name),
                    ["-i", str(Path("/tmp") / name)],
                )


class FinalCompositeOverlayTests(unittest.TestCase):
    def _ffmpeg_cmd(self, overlay_file: str) -> list[str]:
        edit_dir = Path("/tmp/edit")
        overlays = [{"file": overlay_file, "start_in_output": 1.0, "duration": 3.0}]
        with patch.object(render.subprocess, "run") as run:
            render.build_final_composite(
                Path("/tmp/base.mp4"), overlays, None, Path("/tmp/out.mp4"), edit_dir
            )
        return run.call_args.args[0]

    def test_webm_overlay_is_decoded_with_libvpx(self):
        cmd = self._ffmpeg_cmd("/tmp/anim/render.webm")
        i = cmd.index("/tmp/anim/render.webm")
        self.assertEqual(cmd[i - 3 : i], ["-c:v", "libvpx-vp9", "-i"])

    def test_mp4_overlay_keeps_the_default_decoder(self):
        cmd = self._ffmpeg_cmd("/tmp/anim/render.mp4")
        i = cmd.index("/tmp/anim/render.mp4")
        self.assertEqual(cmd[i - 1], "-i")
        self.assertNotIn("libvpx-vp9", cmd)


if __name__ == "__main__":
    unittest.main()
