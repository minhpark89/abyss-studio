"""Record acquisition progress or a reviewed SB09 master in the Second Bell channel."""
from datetime import date
from pathlib import Path
import argparse
import hashlib
import json

EP=Path(__file__).resolve().parent
STUDIO=EP.parents[2]
BASE="production/episodes/SB09/"

def read(path):return json.loads(path.read_text(encoding="utf-8-sig"))
def digest(path):
    with path.open("rb") as f:return hashlib.file_digest(f,"sha256").hexdigest()

def main(finished):
    path=STUDIO/"production/channels/second-bell/checkpoint.json"
    state=read(path)
    receipts=[(p,read(p)) for p in sorted((EP/"receipts").glob("*.json"))]
    verified=[p for p,r in receipts if r.get("status")=="completed" and r.get("media_sha256") and (EP/"takes"/(p.stem+".mp4")).exists()]
    state.update(episode="SB09",title="The Stolen Label",date=date.today().isoformat(),master=None,upload_manifest=None,
                 status=f"Bản làm lại theo Neural Pictures đang dựng. Đã nhận {len(verified)} take Muse có biên nhận.",
                 publication="Bản thử cục bộ cho chủ kênh duyệt.",
                 next="Kiểm hành động trên từng take, dựng ba phút, đo khẩu hình, trộn nhạc và phát hết bản mã hóa trong dashboard.")
    verified_shots={r['shot'] for p,r in receipts if p in verified}
    state["jobs"]=[dict(shot=p.stem,status=r["status"],receipt=BASE+"receipts/"+p.name) for p,r in receipts
                   if r["status"]!="completed" and not (r["status"]=="failed" and r.get("shot") in verified_shots)]
    state["links"].update({"SB09 · đối chiếu cảnh thật với Neural Pictures":BASE+"qa/benchmark/curve.json",
                           "SB09 · kịch bản The Stolen Label":BASE+"story.json","SB09 · tiến độ take Muse":BASE+"qa/production-progress.json",
                           "SB09 · kiểm tay áo, người chứng kiến và phản ứng":BASE+"qa/visual-evidence.json"})
    decision="SB09 thử trường phái Trung Hoa. Muse cung cấp hình và thoại, nhạc và hiệu ứng được tạo cục bộ theo yêu cầu nâng cấp. Giữ bản SB08 để so sánh."
    if decision not in state["decisions"]:state["decisions"].append(decision)
    if finished:
        master=EP/"delivery/The-Stolen-Label.mp4";qa=read(EP/"delivery/QA.json")
        playback=read(EP/"delivery/playback.json");vision=read(EP/"qa/vision.json");audio=read(EP/"delivery/audio-trace.json")
        assert qa["sha256"]==digest(master)==playback["sha256"]==vision["sha256"]==audio["sha256"]
        assert qa["frames"]==4320 and not qa["issues"] and playback["ended"] and vision["passed"]
        state.update(master=dict(kind="excerpt",file=BASE+"delivery/The-Stolen-Label.mp4",report=BASE+"delivery/QA.json"),
                     status="SB09 · The Stolen Label. Đã xuất bản thử 03:00 và kiểm phát hết trong dashboard. Đang chờ chủ kênh duyệt.",
                     next="Chủ kênh xem đoạn nhục mạ mở đầu, bằng chứng dưới ve áo và câu đáp cuối rồi đánh giá độ cuốn hút so với Neural Pictures.")
        state["links"].update({"SB09 · phòng xem":BASE+"delivery/review.html","SB09 · kiểm hình bản xuất":BASE+"qa/vision.json",
                               "SB09 · nhạc, SFX và mức âm lượng trên MP4":BASE+"delivery/audio-trace.json",
                               "SB09 · bằng chứng lệnh":BASE+"delivery/execution_trace.json","SB09 · kiểm phát hết":BASE+"delivery/playback.json"})
        if qa.get("performance_review"):
            trace=read(EP/"delivery/execution_trace.json")
            pacing=read(EP/"qa/cut-continuity/pacing.json")["films"]
            assert trace["sha256"]==qa["performance_review"]["sha256"]==pacing["revision"]["sha256"]==qa["sha256"]
            review=trace["performance_review"]
            state["status"]=(f"SB09 · Bản sửa 03:00 chờ chủ kênh duyệt. Đã kiểm {review['joins']} mối cắt và "
                             f"{review['muted_intervals']} khoảng tắt thoại gốc trên MP4, rồi phát hết trong dashboard. "
                             "Ba take Muse mới nối phản ứng của Alma, câu hỏi bên chiếc áo dựng đứng và động tác kết phim.")
            state["next"]=("Chủ kênh xem ở tốc độ thường từ 00:32 đến 00:41 và từ 02:50 đến hết. "
                           "So bản cũ ở 02:57 với lúc Alma đặt tay lên vai áo trong bản sửa. "
                           "Duyệt nhịp cảm xúc của mẫu trước khi mở rộng tập.")
            state["links"].update({
                "SB09 · bản trước khi sửa":BASE+"prior-cut/2026-11-21/delivery/The-Stolen-Label.mp4",
                "SB09 · kiểm mối cắt và khoảng im lặng":BASE+"qa/cut-continuity/index.html",
                "SB09 · nhịp dựng so với Neural Pictures":BASE+"qa/cut-continuity/pacing.json",
                "SB09 · so tiếng gốc của hai take kết":BASE+"qa/cut-continuity/ending-regression.json"})
            decision=("Đã định vị hai mối nối diễn xuất ở khoảng 00:15 và 00:37 của bản trước. "
                      "Bản sửa chuyển trọng tâm sang phản ứng người nghe và dùng khung từ take trước để nối tay, nét mặt và hướng chỉ. "
                      "Đoạn kết dùng phản ứng im lặng sau câu đáp của Alma.")
            if decision not in state["decisions"]:
                state["decisions"].append(decision)
            cards={s["id"] for s in read(EP/"shots.json")}
            acquired=[r for p,r in receipts if p in verified and digest(EP/"takes"/(p.stem+".mp4"))==r["media_sha256"]]
            completed=cards.intersection(r["shot"] for r in acquired)
            if completed!=cards or state["jobs"]:
                raise ValueError("Reconcile remaining receipt or missing media before release")
            progress=dict(completed=sorted(completed),pending=[],failed={},active=[],
                          completed_takes=len(acquired),selected_pickups=review["corrected_takes"])
            (EP/"qa/production-progress.json").write_text(json.dumps(progress,indent=2)+"\n",encoding="utf8")
            (EP/"qa/final-run-status.json").write_text(json.dumps(dict(status="completed",sha256=qa["sha256"]),indent=2)+"\n",encoding="utf8")
    temp=path.with_suffix(".saving")
    temp.write_text(json.dumps(state,indent=2,ensure_ascii=False)+"\n",encoding="utf8");temp.replace(path)
if __name__=="__main__":
    cli=argparse.ArgumentParser();cli.add_argument("--finished",action="store_true");main(cli.parse_args().finished)
