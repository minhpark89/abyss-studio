"""Regression test for a board that needs both a crop and a pause cut before mastering."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"core/audio_engine")]
from core.project import FF,data,save,sha
from core.assembler.coverage import apply_coverage
from core.muse_bridge.client import compose_prompt
from core.vision_qa.performance import prepare, quiet_intervals, verify
from core.vision_qa.drama_gate import FACETS,review
from core.vision_qa.pickups import select_for_review
from factory import run_episode
from test_mix import fixture

class DramaFactoryTest(unittest.TestCase):
    def test_listener_and_insert_keep_both_native_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            ep=Path(tmp)
            (ep/"take").write_bytes(b"performance fixture")
            cut=dict(shot="A",source="take",source_in=12,source_out=84,start_frame=24,end_frame=96)
            segments=[dict(shot="A",source_in=12,action="She begins speaking.",crop=None),
                      dict(shot="listener",source_in=36,action="He listens.",crop=[0,0,64,36])]
            plan={"A":dict(source_sha256=sha(ep/"take"),segments=segments)}
            speech=[dict(shot="A",start=1.5,end=2.5),dict(shot="A",start=3,end=3.5)]
            left,right=apply_coverage(ep,[cut],speech,plan,24)
            self.assertEqual((left["end_frame"],right["start_frame"],right["end_frame"]),(48,48,96))
            self.assertEqual([c["source_start"] for c in speech],[1,2.5])
            self.assertEqual(list(quiet_intervals(right,speech,24)),[(60,72),(84,96)])
            segments[1]["source_in"]=84
            with self.assertRaisesRegex(ValueError,"outside native picture"):
                apply_coverage(ep,[cut],speech,plan,24)

    def test_continuity_preserves_existing_muse_prompt(self):
        shot=dict(id="A",scene="room",cast=["actor"],action="She looks up.")
        bible=dict(room="Workroom.",actor="Alma.")
        self.assertEqual(compose_prompt(shot,bible),"Workroom. Alma. She looks up.")
        shot["continuity"]=dict(entry="Tear still visible.",exit="Both hands settle.")
        self.assertEqual(compose_prompt(shot,bible),"Workroom. Alma. Tear still visible. She looks up. Both hands settle.")

    def test_observed_crop_compaction_and_failed_pickups(self):
        with tempfile.TemporaryDirectory() as tmp:
            ep=Path(tmp)
            fixture(ep)
            native=ep/"takes/T01.mp4"
            still=ep/"observed.jpg"
            subprocess.run([FF,"-v","error","-i",str(native),"-frames:v","1",str(still)],check=True)
            profile=data(ROOT/"niches/karma-drama/niche.json")
            crop=[32,18,192,108]
            shot=dict(id="T01",source="takes/T01.mp4",receipt="receipts/T01.json",frames=192,in_frame=0,
                      native_dialogue=True,line="Tone test.",beat_id="b",confrontation="b",
                      crop=crop,framing="two_shot_ots",scene="fixture",cast=["A","G"],action="Test chart")
            board=dict(title="Temporary factory integration test",shots=[shot],cast={})
            save(ep/"board.json",board)
            initial=dict(status="completed",task_id="fixture",media_sha256=sha(native))
            save(ep/"receipts/T01.json",initial)
            cue=data(ep/"audio_cues.json");cue["actions"]=[row for row in cue["actions"] if row["start"]==7]
            save(ep/"audio_cues.json",cue)
            proof=dict(sha256=sha(native),sheet="observed.jpg",sheet_sha256=sha(still),cast=["A","G"],
                       approved_spans=[[0,220]],shared_spans=[[0,220]],crop=crop,
                       **{f:{"pass":True,"observation":"Synthetic fixture validates the pipeline only."} for f in FACETS})
            actors=[dict(name=n,imageUrl=still.name,reference_sha256=sha(still),role="lead",cw=100) for n in ["A","G"]]
            path=ep/"qa/visual-evidence.json"
            notes=dict(cast=actors,takes={"T01":proof},confrontations=["b"])
            with self.assertRaisesRegex(ValueError,"Review the completed"):
                select_for_review(ep,"TEST",profile,board,shot,native)
            save(path,notes)
            run_episode(ep,profile,"karma-drama","TEST")
            trace=data(ep/"execution_trace.json");master=ep/trace["master"]
            self.assertEqual(sha(master),trace["sha256"])
            self.assertLess(trace["duration_seconds"],8)
            self.assertEqual(len(trace["audio_engine"]["bgm"]),3)
            self.assertEqual(trace["audio"]["master_measurements"]["decoded_last_20ms_peak"],0)
            self.assertEqual(trace["vision"]["confrontations"]["b"]["shots"],1)
            self.assertTrue(trace["vision"]["passed"])
            screening=ep/"qa/cut-continuity"
            windows=prepare(ep,screening,master)
            decisions={w["id"]:{"decision":"keep","observation":"Synthetic picture fixture."} for w in windows["cases"]}
            self.assertTrue(decisions)
            screening_notes={"windows_sha256":sha(screening/"windows.json"),"observations":decisions}
            save(screening/"review.json",screening_notes)
            self.assertEqual(verify(ep,screening,master)["sha256"],sha(master))
            save(screening/"review.json",{**screening_notes,"observations":{}})
            with self.assertRaisesRegex(ValueError,"Missing or obsolete"):
                verify(ep,screening,master)
            save(screening/"review.json",{**screening_notes,"windows_sha256":"stale"})
            with self.assertRaisesRegex(ValueError,"another cut or mix"):
                verify(ep,screening,master)
            self.assertEqual({v["repo"] for v in trace["commands"] if v.get("stage")=="audio_mixing"},
                             {"spotify/pedalboard","slhck/ffmpeg-normalize"})
            self.assertTrue(all(row["sha256"] for row in trace["audio_engine"]["sfx"]))
            plan=data(ep/"work/edit.json")
            proof["shared_spans"]=[];save(path,notes)
            with self.assertRaisesRegex(ValueError,"too few"):
                review(ep,master,plan["cuts"],path,ep/"qa/second.json")
            proof["hands_and_wardrobe"]["pass"]=False
            save(path,notes)
            def replacement(card,cast,replacement,*,root,**kwargs):
                shutil.copyfile(native,root/"takes"/(replacement+".mp4"))
                save(root/"receipts"/(replacement+".json"),{**initial,"take":replacement})
            with patch("core.vision_qa.pickups.acquire",side_effect=replacement) as client:
                for _ in range(2):
                    with self.assertRaisesRegex(ValueError,"Review the new native take"):
                        select_for_review(ep,"TEST",profile,board,shot,native)
                self.assertEqual(client.call_args_list[0],client.call_args_list[1])
            print("Temporary factory master",trace["duration_seconds"],trace["audio"]["master_measurements"],trace["vision"]["confrontations"])

if __name__=="__main__":unittest.main()
