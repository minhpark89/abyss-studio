"""Compile the editorial timing, character locks and causal board for SB09."""
from board import cards
from board_seed import CAST, save

production = dict(project_key="second-bell/SB09/the-stolen-label", project_title="SB09 | The Stolen Label")
props = dict(coat="Royal-blue wool show coat on a headless tan dress form. Under its left lapel a gold embroidered crane appears against cream lining.",
             labels="A removable cream maker's label is replaced on the outside with a black clip-on label. Neither requires reading.",
             portfolio="Alma's cream portfolio contains loose ivory costume sketches. They remain on the floor after Gavin knocks them down.",
             badge="Gavin's small plain silver square badge. He surrenders it at the oak workbench after Nina fires him.",
             folder="Nina's closed navy commission folder for the forty-coat order. Final recipient is Alma.")
assets=[dict(id=k,kind="location" if k=="atelier" else "character",anchor=v,reference_files={"A":["refs/alma.jpg"],"G":["refs/gavin.jpg"],"N":["refs/nina.jpg"],"atelier":["refs/ag.jpg"]}[k]) for k,v in CAST.items()]
assets.extend(dict(id=k,kind="prop",anchor=v) for k,v in props.items())
rows=[
 ("pending","threatened","Gavin knocks the drawings from Alma's hands and puts a shoe over her work.","Alma discovers he means to take payment for the entire forty-coat order.","Humiliation and anger","Keep both bodies in the opening frame. Lower the camera with the scattered page, then find both faces."),
 ("threatened","false_label","Gavin tears off the maker's label, threatens her job and attaches his own black tag.","The outside of the coat now supports his lie, but Alma has seeded a permanent mark beneath the lapel.","Alarm and calculation","Hold the relationship through his threat. The first insert is his burgundy cuff and a black clip, not an anonymous hand."),
 ("false_label","false_prediction","He claims the commission before Nina. Alma asks her to test him. Gavin predicts plain silk and tries to pack the coat away.","Removing the sample would prevent the buyer from seeing the proof.","Disbelief becoming suspense","OTS follows the person asking for an answer. Let the coat and receiving face occupy one space."),
 ("false_prediction","proof","Alma risks being fired, names a hidden gold crane, and makes Nina open the lapel herself.","The buyer has seen something only the maker predicted before the lining was visible.","Defiance, discovery and recognition","Hold the closed lapel before Nina opens it. Only one unveiling. Return to the face of the person who actually saw it."),
 ("proof","bribe","Gavin claims ownership of the maker herself, offers Nina a kickback, then threatens Alma again.","Nina has personally heard his bribe and seen the theft. Gavin still refuses to back down.","Anger rising to disgust","Use two-shots to hold the reaction to each escalation. Keep the navy folder shut."),
 ("bribe","transferred","Nina publicly dismisses Gavin. His badge lands on the workbench. Nina hands the whole order to Alma.","Alma now owns the contract. She returns his words and stands at her own coat as he loses his status.","Consequences, vindication, release","See badge leave the burgundy jacket, folder transfer to copper cuffs, then the returned line and Alma's face.")]
beats=[];directions={};clock=0
for i,(before,after,action,effect,mood,camera) in enumerate(rows,1):
 key=f"B{i:02d}"
 shots=[c for c in cards if c["beat_id"]==key]
 length=sum(s["duration_seconds"] for s in shots)
 beats.append(dict(id=key,cause=None if i==1 else f"B{i-1:02d}",action=action,effect=effect,requires={"order":before},changes={"order":after},shots=[s["id"] for s in shots],start_seconds=clock,end_seconds=clock+length))
 directions[key]=dict(mood=mood,camera_movement=camera)
 clock+=length
assert clock==180 and beats[-1]["start_seconds"]>=144
save("story.json", dict(episode="SB09",title="The Stolen Label",fps=24,duration_seconds=180,profile="cn",renderer="Muse",language="en-US",aspect_ratio="16:9",production=production,stakes="Alma risks losing her job if she claims the forty-coat order she earned.",choice="Stay employed under someone else's name or risk her job on a hidden mark only she knows.",consequence="The commissioner fires Gavin and gives the tour commission directly to Alma.",assets=assets,initial_state={"order":"pending"},beats=beats))
roles={
 "conflict":("T01","Gavin deliberately knocks down Alma's portfolio and humiliates her."),
 "proof":("T16","Nina's navy cuff follows her hand to the blue lapel. She opens it herself and a stitched gold crane appears."),
 "cost":("T20","Gavin slides the contract toward Nina, offering her ten percent to leave Alma unpaid."),
 "choice":("T23","In Alma's presence Nina fires him and points to the bench for his badge."),
 "visible_consequence":("T25","Alma receives the navy folder holding the entire order from the commissioner.")}
save("direction.json",dict(production=production,source_duration_seconds=10,roles={k:dict(shot=s,on_screen=a) for k,(s,a) in roles.items()},beats=directions,shots={c["id"]:{"duration_seconds":10} for c in cards},joins=[
 {"shots":["T01","T02"],"inspect":"Sketches already on the floor at the second angle."},
 {"shots":["T04","T05","T07"],"inspect":"Cream label removed once before black tag is attached. No repeated rip."},
 {"shots":["T15","T16","T17"],"inspect":"Prediction precedes opening; gold on pale lining only after the opening. No repeated reveal."},
 {"shots":["T23","T24","T25","T26"],"inspect":"Nina demands badge; Gavin lays it down; Nina transfers folder; only then does Alma deliver callback."}]))
