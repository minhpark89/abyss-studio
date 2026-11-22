"""Exercise a real mux/decode and the failed-native-handle path in a temporary episode."""
from pathlib import Path
import json
import tempfile
import unittest
import subprocess
from mix_episode import FF,render,empty_gaps
from fetch_sfx import cc0
from core.audio_cleaner.compact_timeline import compact

def fixture(root):
    takes=root/"takes";takes.mkdir()
    native=takes/"T01.mp4"
    subprocess.run([FF,"-nostdin","-v","error","-y","-f","lavfi","-i","testsrc2=size=256x144:rate=24",
                    "-f","lavfi","-i","sine=frequency=310:sample_rate=48000","-t","10","-c:v","libx264","-preset","ultrafast","-c:a","aac",str(native)],check=True)
    subprocess.run([FF,"-nostdin","-v","error","-y","-i",str(native),"-t","8","-an","-c:v","libx264","-preset","ultrafast",str(root/"picture.mp4")],check=True)
    plan={"fps":24,"cuts":[{"shot":"T01","source":"takes/T01.mp4","source_in":0,"source_out":192,"start_frame":0,"end_frame":192,"line":"Dialogue fixture."}]}
    cues={"niche":"karma-drama","music":[{"cue":"tense_bed","at":0},{"cue":"dark_escalation","at":2},{"cue":"karma_payoff","at":5}],
        "sfx":[{"at":2.5,"cue":"riser_2s"}],"twist_reveal_timestamp":5,"speech":[{"shot":"T01","start":.3,"end":2,"text":"Fixture line."},
                     {"shot":"T01","start":5,"end":7,"text":"Fixture callback."}],
        "actions":[{"start":2,"end":5,"action":"The trial pattern visibly moves."},{"start":7,"end":8,"action":"The final gesture finishes."}]}
    (root/"edit.json").write_text(json.dumps(plan));(root/"audio_cues.json").write_text(json.dumps(cues))
    return plan

class MixTest(unittest.TestCase):
    def test_mux_and_bad_handles(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);plan=fixture(root);trace=render(root,"picture.mp4","delivery/review.mp4")
            self.assertAlmostEqual(trace["score_relative_to_dialogue_db"],-24,places=1)
            self.assertEqual(trace["master_measurements"]["decoded_last_20ms_peak"],0)
            self.assertEqual(trace["master_measurements"]["decoded_silence_drop_core_peak"],0)
            print("Decoded master",trace["master_measurements"],"voice/music",trace["score_relative_to_dialogue_db"])
            plan["cuts"][0]["source_out"]=239
            (root/"edit.json").write_text(json.dumps(plan))
            with self.assertRaisesRegex(ValueError,"safe window"):render(root,"picture.mp4","delivery/review.mp4")
    def test_idle_gap_and_rights(self):
        self.assertEqual(empty_gaps(0,4,[(0,1),(1.7,2),(3.5,4)]),[(2.8,3.5)])
        self.assertTrue(cc0("http://creativecommons.org/publicdomain/zero/1.0/"))
        self.assertFalse(cc0("https://creativecommons.org/licenses/by/4.0/"))
        self.assertFalse(cc0("https://example.org/publicdomain/zero/1.0/"))
    def test_compaction_moves_picture_dialogue_and_twist_together(self):
        plan={"fps":25,"cuts":[dict(start_frame=0,end_frame=150,source_in=10,source_out=160)]}
        cues={"speech":[{"start":0,"end":1},{"start":4,"end":6}],"twist_reveal_timestamp":4,
              "music":[{"at":0},{"at":4}],"sfx":[{"at":4}]}
        edit,sound,removed=compact(plan,cues)
        self.assertEqual(removed,[(45,87)])
        self.assertEqual(edit["cuts"][1]["source_in"],97)
        self.assertEqual(edit["cuts"][1]["start_frame"],45)
        self.assertEqual(sound["speech"][1]["start"],sound["twist_reveal_timestamp"])
        self.assertEqual(sound["sfx"][0]["at"],sound["music"][1]["at"])

if __name__=="__main__":unittest.main()
