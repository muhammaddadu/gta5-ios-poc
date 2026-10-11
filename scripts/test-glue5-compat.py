#!/usr/bin/env python3
"""Compile tests against the actual locally patched layout and touch expressions."""
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'.local/upstream/glue5-integrated'
OUT = ROOT/'.local/glue5-tests'
OUT.mkdir(parents=True,exist_ok=True)
lock=json.loads((ROOT/'upstreams.json').read_text())
rust=lock['glue5_integration']['rust']
build=lock['engine']['build']
text=(SOURCE/'crates/glue5-runtime/src/lib.rs').read_text()
a=text.index('pub mod layout {');b=text.index('\nuse crate::memory',a)
# Generated tests and the verbatim private dependency module stay under .local/.
layout=f'const GAME_BUILD: &str = "{build}";\n'+text[a:b]+'''
#[test]
fn complete_layouts_only() {
 let base=std::env::temp_dir().join(format!("gtapoc-layout-{}",std::process::id()));
 std::fs::create_dir_all(base.join("data")).unwrap();
 let modern=base.join("b").join(GAME_BUILD).join("shaders");
 std::fs::create_dir_all(&modern).unwrap();std::fs::write(modern.join("index.json"),"{}").unwrap();
 assert!(!layout::is_game_dir(&base));
 std::fs::write(base.join("data/manifest.json"),"{}").unwrap();
 assert!(layout::is_game_dir(&base));assert_eq!(layout::shader_dir(&base),modern);
 let legacy=base.join("shaders");std::fs::create_dir_all(&legacy).unwrap();std::fs::write(legacy.join("index.json"),"{}").unwrap();
 assert!(layout::is_game_dir(&base));assert_eq!(layout::shader_dir(&base),legacy);
 std::fs::remove_dir_all(base).unwrap();
}
'''
text=(SOURCE/'crates/glue5/src/touch.rs').read_text()
expr=re.search(r'self\.pos\(b\.at\)\.distance\(p\) <= ([^\n]+)',text)[1]
expr=expr.replace('b.radius','radius').replace('self.scale','scale')
touch='fn target(radius:f32,scale:f32)->f32 { '+expr+' }\n'+'''
#[test]
fn usable_small_button_targets() {
 for scale in [0.4,0.82,1.0,1.5] {for radius in [18.0,20.0,22.0,25.0,28.0] {
  assert!(target(radius,scale)*2.0>=44.0);
 }}
 assert_eq!(target(28.0,1.0),35.0);
}
'''
for name,code in [('layout',layout),('touch-target',touch)]:
 source=OUT/(name+'.rs');binary=OUT/(name+'-test');source.write_text(code)
 subprocess.run(['mise','exec','rust@'+rust,'--','rustc','--test',str(source),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True)
