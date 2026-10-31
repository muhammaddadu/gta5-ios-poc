#!/usr/bin/env python3
"""Exercise the patched private Rust resize method with synthetic window/input seams."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
source = ROOT/'.local/upstream/glue5-integrated/crates/glue5/src'
out = ROOT/'.local/glue5-tests'
out.mkdir(parents=True, exist_ok=True)
text = (source/'app.rs').read_text()
a = text.index('    fn update_game_rect(')
b = text.index('    /// Starts the game;', a)
method = text[a:b].replace('log::info!', 'noop!')
text = (source/'settings.rs').read_text()
a = text.index('pub fn render_size(')
b = text.index('\n#[cfg(test)]', a)
render = text[a:b]
# All verbatim upstream fragments and generated binaries stay ignored.
harness = r'''
use std::cell::Cell;
use std::sync::Mutex;
#[path="DUO_LAYOUT"] mod duo_layout;
const MOBILE: bool = true;
macro_rules! noop { ($($t:tt)*) => {}; }
#[derive(Default)] struct Gamepad;
mod glue5_runtime { pub mod input {
    pub fn set_gamepad(_: u32, _: crate::Gamepad) {}
}}
mod settings { use crate::MOBILE; RENDER }
mod ui {pub fn handheld_layout(w:&crate::Window,touch:bool)->crate::duo_layout::Layout {let(w,h)=w.size();crate::duo_layout::layout(w as f32,h as f32,[0.;4],touch)}}
struct Shared {game_rect:Mutex<Option<[f32;4]>>}
struct Presentation(Shared);
impl Presentation { PRESENTATION }
enum TouchMode {Auto,Always,Off}
struct Window { pixels: (u32,u32) }
impl Window { fn size_in_pixels(&self)->(u32,u32) { self.pixels } fn size(&self)->(u32,u32) {(self.pixels.0/3,self.pixels.1/3)} }
struct Settings { scale: f32, touch:TouchMode }
impl Settings { fn render_scale(&self)->f32 { self.scale } }
#[derive(Default)] struct Input { released: Cell<u32>, sizes: Cell<(u32,u32)> }
impl Input {
 fn release_all(&self) { self.released.set(self.released.get()+1); }
 fn resize(&self,w:u32,h:u32) { self.sizes.set((w,h)); }
}
struct Started { render_scale: f32, low_memory: bool }
struct Game { input: Option<Input>, started: Started, back_buffer: (u32,u32) }
#[derive(Default)] struct Touch { cleared: u32 }
impl Touch { fn clear(&mut self) { self.cleared+=1; } }
struct App { game: Option<Game>, window: Window, settings: Settings, touch: Touch, presentation:Presentation, touch_input:bool }
impl App { METHOD }
fn app()->App {
 App { game: Some(Game {input:Some(Input::default()),
 started: Started {render_scale:0.5,low_memory:true}, back_buffer:(0,0)}),
 window:Window {pixels:(2034,1398)},settings:Settings {scale:1.0,touch:TouchMode::Auto},touch:Touch::default(), presentation:Presentation(Shared{game_rect:Mutex::new(None)}),touch_input:true }
}
#[test] fn fold_unfold_and_return_keep_aspect_and_release_input() {
 let mut app=app();
 // Cover, inner landscape, inner portrait, cover: changing live window dimensions.
 for pixels in [(2034,1398),(2670,1878),(1878,2670),(2034,1398)] {
  app.window.pixels=pixels; app.resize_game();
  let game=app.game.as_ref().unwrap();
  let expected=settings::render_size(app.presentation.game_area_size(pixels),0.5,true);
  assert_eq!(game.back_buffer,expected);
  assert_eq!(game.input.as_ref().unwrap().sizes.get(),expected);
 }
 assert_eq!(app.touch.cleared,4);
 assert_eq!(app.game.as_ref().unwrap().input.as_ref().unwrap().released.get(),4);
 app.resize_game(); assert_eq!(app.touch.cleared,4); // unchanged size must not rebuild
}
#[test] fn zero_window_and_missing_engine_input_do_not_submit_resize() {
 let mut app=app();app.window.pixels=(0,0);app.resize_game();
 assert_eq!(app.touch.cleared,0);
 app.window.pixels=(2670,1878);app.game.as_mut().unwrap().input=None;
 app.resize_game();assert_eq!(app.touch.cleared,0);
 app.game=None;app.resize_game();
}

#[test] fn controller_mode_reclaims_the_portrait_scene() {
 let mut app=app();app.window.pixels=(1878,2670);app.resize_game();
 assert!(app.presentation.game_area_size(app.window.pixels).1<2670);
 app.settings.touch=TouchMode::Off;app.resize_game();
 assert_eq!(app.presentation.game_area_size(app.window.pixels),app.window.pixels);
 app.settings.touch=TouchMode::Always;app.touch_input=false;app.resize_game();
 assert!(app.presentation.game_area_size(app.window.pixels).1<2670);
 app.settings.touch=TouchMode::Auto;app.resize_game();
 assert_eq!(app.presentation.game_area_size(app.window.pixels),app.window.pixels);
}
#[test] fn mobile_low_memory_workload_stays_bounded_and_even() {
 for pixels in [(2670,1878),(1878,1548),(2034,1398),(6000,4000)] {
  let (w,h)=settings::render_size(pixels,1.0,true);
  assert!(w as u64*h as u64<=1_510_000);assert_eq!(w%2,0);assert_eq!(h%2,0);
  assert!((w as f32/h as f32-pixels.0 as f32/pixels.1 as f32).abs()<0.01);
 }
}

#[test] fn final_presenter_fills_the_scene_region_without_hiding_it_under_controls() {
 let mut app=app();
 for pixels in [(2670,1878),(1878,2670),(2034,1398)] {
  app.window.pixels=pixels;app.resize_game();
  let area=app.presentation.game_area(pixels);
  let game=app.game.as_ref().unwrap();
  let (x,y,w,h)=fit(game.back_buffer,(area.2,area.3));
  assert_eq!((x,y),(0,0));assert_eq!((w,h),(area.2,area.3));
  assert!(area.1+h<=pixels.1);
 }
}
'''.replace('RENDER', render).replace('METHOD', method).replace('DUO_LAYOUT',str(ROOT/'scripts/duo-layout.rs'))
present=(ROOT/'.local/upstream/glue5-integrated/crates/glue5-gpu/src/present.rs').read_text()
a=present.index('    pub fn set_game_rect(');b=present.index('    pub fn set_vsync(',a)
harness=harness.replace('PRESENTATION',present[a:b])
a=present.index('fn fit(');b=present.index('\n/// The window',a)
harness=present[a:b]+'\n'+harness
path = out/'mobile-resize.rs'
path.write_text(harness)
rust = json.loads((ROOT/'upstreams.json').read_text())['glue5_integration']['rust']
binary = out/'mobile-resize-test'
subprocess.run(['mise','exec','rust@'+rust,'--','rustc','--edition=2024','--test',str(path),'-o',str(binary)],check=True)
subprocess.run([str(binary)],check=True)
