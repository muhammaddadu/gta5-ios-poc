#!/usr/bin/env python3
"""Render actual private native touch shapes into an asset-free browser preview."""
from pathlib import Path
import argparse
import http.server
import json
import subprocess
import urllib.parse
from duo_preview_pages import extend

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.local/duo-preview'
SOURCE=ROOT/'.local/upstream/glue5-integrated'


def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'src').mkdir(exist_ok=True)
    # This private harness compiles the real touch module, with a synthetic input backend.
    (OUT/'Cargo.toml').write_text('[package]\nname="gta-duo-preview"\nversion="0.1.0"\nedition="2024"\n[dependencies]\negui="=0.36.2"\nserde_json="1"\nserde={version="1",features=["derive"]}\npng="0.18"\nlog="0.4"\n')
    code=r'''
#![allow(dead_code)]
extern crate self as glue5_runtime;
pub mod input {
 #[derive(Default)] pub struct Gamepad {pub connected:bool,pub buttons:u16,pub left:[f32;2],pub right:[f32;2],pub l2:f32,pub r2:f32}
 pub mod button {
  pub const UP:u16=1;pub const DOWN:u16=2;pub const LEFT:u16=4;pub const RIGHT:u16=8;
  pub const SOUTH:u16=16;pub const EAST:u16=32;pub const WEST:u16=64;pub const NORTH:u16=128;
  pub const L1:u16=256;pub const R1:u16=512;pub const L2:u16=1024;pub const R2:u16=2048;
  pub const L3:u16=4096;pub const R3:u16=8192;pub const START:u16=16384;pub const SELECT:u16=32768;
 }
}
#[path="LAYOUT"] mod duo_layout;
#[path="TOUCH"] mod touch;
use egui::{Color32,Shape};
use serde_json::{json,Value};
fn color(c:Color32)->Value {let [r,g,b,a]=c.to_srgba_unmultiplied();json!([r,g,b,a as f32/255.0])}
fn shape(s:&Shape)->Value { match s {
 Shape::Circle(c)=>json!({"t":"circle","x":c.center.x,"y":c.center.y,"r":c.radius,"fill":color(c.fill),"stroke":color(c.stroke.color),"sw":c.stroke.width}),
 Shape::Rect(r)=>json!({"t":"rect","x":r.rect.min.x,"y":r.rect.min.y,"w":r.rect.width(),"h":r.rect.height(),"fill":color(r.fill),"stroke":color(r.stroke.color),"sw":r.stroke.width}),
 Shape::Path(p)=>json!({"t":"path","points":p.points.iter().map(|p|[p.x,p.y]).collect::<Vec<_>>(),"closed":p.closed,"fill":color(p.fill),"stroke":color(match p.stroke.color {egui::epaint::ColorMode::Solid(c)=>c,_=>Color32::WHITE}),"sw":p.stroke.width}),
 Shape::LineSegment{points,stroke}=>json!({"t":"path","points":points.iter().map(|p|[p.x,p.y]).collect::<Vec<_>>(),"closed":false,"fill":[0,0,0,0],"stroke":color(stroke.color),"sw":stroke.width}),
 Shape::Text(t)=>{
  let Some(section)=t.galley.job.sections.first() else {return json!({"t":"none"})};
  let f=&section.format;let fill=t.override_text_color.unwrap_or(if f.color==Color32::PLACEHOLDER{t.fallback_color}else{f.color});
  let font=if matches!(&f.font_id.family,egui::FontFamily::Name(n) if n.as_ref()=="condensed"){"DuoCondensed"}else{"DuoUI"};
  let mut glyphs=Vec::new();for row in &t.galley.rows {for g in &row.glyphs {
   glyphs.push(json!({"t":"text","x":t.pos.x+row.pos.x+g.pos.x,"y":t.pos.y+row.pos.y+g.pos.y,
    "text":g.chr.to_string(),"size":f.font_id.size,"baseline":true,"font":font,"fill":color(fill)}));
  }}json!({"t":"group","shapes":glyphs})
 },
 Shape::Vec(v)=>json!({"t":"group","shapes":v.iter().map(shape).collect::<Vec<_>>()}),
 _=>json!({"t":"none"})
}}
fn main(){
 let args=std::env::args().collect::<Vec<_>>();let w=args[1].parse::<f32>().unwrap();let h=args[2].parse::<f32>().unwrap();
 let controller=args.get(3).is_some_and(|s|s=="controller");let action=args.get(4).map(String::as_str).unwrap_or("");
 let l=duo_layout::layout(w,h,[12.,10.,12.,22.],!controller);
 let area=egui::Rect::from_min_size(egui::pos2(l.controls.x,l.controls.y),egui::vec2(l.controls.w,l.controls.h));
 let mut t=touch::Touch::new();t.layout(egui::vec2(w,h),area,1.0);
 let scale=if l.deck {duo_layout::deck_scale(l.controls,1.)}else{if w.min(h)<500.{0.82}else{1.}};
 let id=match action {"A"=>Some(0),"move"=>Some(12),"camera"=>Some(13),_=>action.parse::<usize>().ok().filter(|i|*i<15)};
 if let Some(id)=id {let c=duo_layout::control(id,l.controls,scale,l.deck);t.finger_down(1,c.x/w,c.y/h);
  if id>=12 {t.finger_motion(1,(c.x+c.r*0.5)/w,c.y/h);}}
 let ctx=egui::Context::default();ctx.begin_pass(egui::RawInput{screen_rect:Some(egui::Rect::from_min_size(egui::Pos2::ZERO,egui::vec2(w,h))),..Default::default()});
 if !controller {t.draw(&ctx.layer_painter(egui::LayerId::background()),0.8);}
 let output=ctx.end_pass();let pad=t.gamepad();
 let mut circles=Vec::new();for id in 0..16 {let c=duo_layout::control(id,l.controls,scale,l.deck);circles.push(json!({"x":c.x,"y":c.y,"r":c.r}));}
 println!("{}",json!({"w":w,"h":h,"deck":l.deck,"game":[l.game.x,l.game.y,l.game.w,l.game.h],"controls":[l.controls.x,l.controls.y,l.controls.w,l.controls.h],"shapes":output.shapes.iter().map(|s|shape(&s.shape)).collect::<Vec<_>>(),"circles":circles,"buttons":pad.buttons,"left":pad.left,"right":pad.right}));
}
'''.replace('LAYOUT',str(ROOT/'scripts/duo-layout.rs')).replace('TOUCH',str(SOURCE/'crates/glue5/src/touch.rs'))
    code=extend(code,SOURCE)
    (OUT/'src/main.rs').write_text(code)
    subprocess.run(['mise','exec','rust@1.99.0','--','cargo','build','--manifest-path',str(OUT/'Cargo.toml')],check=True)


def prepare_portable():
    """Build only original platform-neutral Rust geometry; no Apple SDK required."""
    OUT.mkdir(parents=True,exist_ok=True)
    code=r'''
#[path="LAYOUT"] mod duo_layout;
static mut OUTPUT:[f32;58]=[0.;58];
#[unsafe(no_mangle)] pub extern "C" fn check_geometry()->u32 {duo_layout::geometry_report().1}
#[unsafe(no_mangle)] pub extern "C" fn check_cases()->u32 {duo_layout::geometry_report().0}
#[unsafe(no_mangle)] pub extern "C" fn compute(w:f32,h:f32,touch:u32) {
 let l=duo_layout::layout(w,h,[12.,10.,12.,22.],touch!=0);
 let s=if l.deck {duo_layout::deck_scale(l.controls,1.)}else{if w.min(h)<500.{0.82}else{1.}};
 let mut out=[0.;58];out[0]=if l.deck{1.}else{0.};
 out[1..5].copy_from_slice(&[l.game.x,l.game.y,l.game.w,l.game.h]);
 out[5..9].copy_from_slice(&[l.controls.x,l.controls.y,l.controls.w,l.controls.h]);
 for id in 0..16 {let c=duo_layout::control(id,l.controls,s,l.deck);out[9+id*3]=c.x;out[10+id*3]=c.y;out[11+id*3]=c.r;}
 out[57]=s;unsafe{OUTPUT=out;}
}
#[unsafe(no_mangle)] pub extern "C" fn buffer()->*const f32 { (&raw const OUTPUT).cast::<f32>() }
'''.replace('LAYOUT',str(ROOT/'scripts/duo-layout.rs'))
    path=OUT/'geometry.rs';path.write_text(code)
    subprocess.run(['mise','exec','rust@1.99.0','--','rustc','--edition=2024',
        '--target','wasm32-unknown-unknown','--crate-type','cdylib','-O',str(path),
        '-o',str(OUT/'geometry.wasm')],check=True)


class Handler(http.server.BaseHTTPRequestHandler):
    portable=False
    def do_GET(self):
        route=urllib.parse.urlparse(self.path)
        if route.path=='/mode':
            body=json.dumps({'portable':self.portable}).encode();mime='application/json'
        elif route.path=='/geometry.wasm':
            body=(OUT/'geometry.wasm').read_bytes();mime='application/wasm'
        elif route.path in ('/font/regular.ttf','/font/condensed.ttf'):
            name='Barlow-SemiBold.ttf' if route.path=='/font/regular.ttf' else 'BarlowCondensed-Bold.ttf'
            body=(SOURCE/'crates/glue5/assets/ui'/name).read_bytes();mime='font/ttf'
        elif route.path=='/layout':
            q=urllib.parse.parse_qs(route.query)
            w=max(320,min(1400,float(q.get('w',['626'])[0])))
            h=max(320,min(1400,float(q.get('h',['890'])[0])))
            mode=q.get('mode',['touch'])[0];action=q.get('action',[''])[0]
            body=subprocess.check_output([str(OUT/'target/debug/gta-duo-preview'),str(w),str(h),mode,action])
            mime='application/json'
        elif route.path in ('/','/duo-preview.html'):
            body=(ROOT/'web/duo-preview.html').read_bytes();mime='text/html; charset=utf-8'
        else:
            self.send_error(404);return
        self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def log_message(self,*args): pass


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--portable',action='store_true');parser.add_argument('--build-only',action='store_true');parser.add_argument('--port',type=int,default=8091);a=parser.parse_args()
    if a.portable:
        prepare_portable();Handler.portable=True
    else:
        prepare()
    if not a.build_only:
        print(f'Native touch preview: http://127.0.0.1:{a.port}',flush=True)
        http.server.ThreadingHTTPServer(('127.0.0.1',a.port),Handler).serve_forever()
