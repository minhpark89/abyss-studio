"""Small, offline regression run: generated fixture media lives only in a temporary directory."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from components import ROOT, read, sha
from pipeline import dump, execute
from storyboard import board


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.ep = Path(self.temp.name)
        self.story = dict(title="Fixture", initial_state={"open":True}, duration_seconds=2,
                          assets=[dict(id="room",kind="location",anchor="yellow room")],
                          beats=[dict(id="b1",cause=None,action="Close the desk",effect="Appeal required",
                                      requires={"open":True},changes={"open":False},shots=["s1"]),
                                 dict(id="b2",cause="b1",action="Grant appeal",effect="Hear contestant",
                                      requires={"open":False},changes={"open":True},shots=["s2"])])
        self.cards = [dict(id=s,scene="room",framing="wide",action=s,cut_reason="Witness responds") for s in ("s1","s2")]
        dump(self.ep/"story.json",self.story)
        dump(self.ep/"shots.json",self.cards)

    def test_causal_break(self):
        self.story["beats"][1]["requires"]["open"] = True
        with self.assertRaisesRegex(ValueError,"unsatisfied"):
            board(self.story,self.cards,{}, {})

    def test_missing_coverage(self):
        with self.assertRaisesRegex(ValueError,"unknown shot"):
            board(self.story,self.cards[:1],{}, {})

    def test_render_review_resume_and_changed_receipt(self):
        ffmpeg = shutil.which("ffmpeg") or ROOT.parent/"abyss-studio/tools/ffmpeg-nvenc/ffmpeg.exe"
        (self.ep/"takes").mkdir()
        (self.ep/"receipts").mkdir()
        cuts = []
        for i, color in enumerate(("red","blue"),1):
            sid = f"s{i}"
            path = self.ep/"takes"/(sid+".mp4")
            subprocess.run([str(ffmpeg),"-v","error","-f","lavfi","-i",f"color=c={color}:s=128x72:r=24:d=1",
                            "-f","lavfi","-i","anullsrc=r=48000:cl=mono","-t","1","-c:v","libx264","-c:a","aac",
                            str(path)],check=True)
            dump(self.ep/"receipts"/(sid+".json"),dict(shot=sid,status="completed",task_id="fixture-"+sid,media_sha256=sha(path)))
            cuts.append(dict(shot=sid,source="takes/"+path.name,source_in=0,source_out=24))
        (self.ep/"list.txt").write_text("file 'takes/s1.mp4'\nfile 'takes/s2.mp4'\n")
        subprocess.run([str(ffmpeg),"-v","error","-f","concat","-safe","0","-i",str(self.ep/"list.txt"),
                        "-c","copy",str(self.ep/"master.mp4")],check=True)
        dump(self.ep/"edit.json",dict(fps=24,master="master.mp4",cuts=cuts))
        output = execute("review",self.ep,"cn",None)
        report = read(output)
        self.assertTrue(all(c["executed"] for c in report["components"]))
        self.assertEqual(report["media"]["frames"],48)
        self.assertEqual(len(report["media"]["source_to_master_samples"]),2)
        self.assertEqual(execute("review",self.ep,"cn",None), output)
        receipt = self.ep/"receipts/s1.json"
        corrupt = read(receipt)
        corrupt["media_sha256"] = "bad"
        dump(receipt,corrupt)
        with self.assertRaisesRegex(ValueError,"Unverified Muse take"):
            execute("review",self.ep,"cn",None)


if __name__ == "__main__":
    unittest.main()
