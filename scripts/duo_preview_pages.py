"""Synthetic platform seams for rendering/testing the actual private native pages."""


def item(source, signature):
    start=source.index(signature);brace=source.index('{',start);depth=1;end=brace+1
    while depth:
        depth += (source[end]=='{')-(source[end]=='}');end+=1
    return source[start:end]


def extend(code, source):
    text=(source/'crates/glue5/src/ui.rs').read_text()
    definitions='\n'.join([
        '#[derive(Clone,Copy,Debug,PartialEq,Eq)]\n'+item(text,'pub enum Page'),
        item(text,'pub enum Action'),item(text,'pub struct Started'),
        item(text,"pub struct Status<'a>"),
        '#[derive(Clone,Copy,Default,PartialEq,Eq)]\n'+item(text,'enum SettingsTab'),
    ])
    extra=r'''
extern crate self as sdl3;
pub mod cpuinfo {pub fn system_ram()->i32 {6000}}
mod paths {
 pub const MOBILE:bool=true;
 pub fn where_the_game_goes()->&'static str {"Documents/data and Documents/shaders"}
 pub fn game_layout()->&'static str {"data/manifest.json + shaders/index.json"}
}
#[path="SETTINGS"] mod settings;
mod ui {
 use std::path::{Path,PathBuf};use egui::Color32;
 #[path="PAGES"] mod pages;
 #[path="WIDGETS"] mod widgets;
 #[path="THEME"] pub mod theme;
 const WARN:Color32=Color32::from_rgb(240,180,100);
 DEFINITIONS
 pub fn setup(ctx:&egui::Context){theme::install(ctx);}
 pub fn draw(ctx:&egui::Context,mode:&str){
  let mut settings=crate::settings::Settings::default();settings.start_mode=2;settings.low_memory=true;settings.for_screen((ctx.viewport_rect().height()*3.0) as u32);
  let full=ctx.viewport_rect();let region=crate::duo_layout::layout(full.width(),full.height(),[12.0,10.0,12.0,22.0],true);
  let status=Status{game_dir:if mode=="missing"{None}else{Some(Path::new("synthetic/game"))},problem:Some("Copy the complete matching game files, then recheck."),started:None,
   last_failure:None,graphics_reset:false,window:((region.game.w*3.0) as u32,(region.game.h*3.0) as u32),metalfx:true,metal_hud:false,refresh_rate:120.0};
  if mode=="home"||mode=="missing" {
   pages::start_page(ctx,&status,&mut settings,false,&mut Vec::new(),&mut None);
  }else{
   let mut tab=if mode=="controls"{SettingsTab::Controls}else{SettingsTab::Video};
   pages::settings_page(ctx,&mut settings,&status,None,&mut tab,&mut None,&mut Vec::new());
  }
 }
}
'''.replace('DEFINITIONS',definitions)
    for key,path in [('SETTINGS','settings.rs'),('PAGES','ui/pages.rs'),('WIDGETS','ui/widgets.rs'),('THEME','ui/theme.rs')]:
        extra=extra.replace(key,str(source/'crates/glue5/src'/path))
    code=code.replace('use egui::{Color32,Shape};',extra+'\nuse egui::{Color32,Shape};')
    code=code.replace('"h":r.rect.height(),"fill"','"h":r.rect.height(),"rx":r.corner_radius.nw,"fill"')
    code=code.replace('"size":f.font_id.size,"fill"','"size":f.font_id.size,"font":if matches!(&f.font_id.family,egui::FontFamily::Name(n) if n.as_ref()=="condensed"){"DuoCondensed"}else{"DuoUI"},"fill"')
    old='let output=ctx.end_pass();let pad=t.gamepad();'
    new=r'''let mut output=ctx.end_pass();output.textures_delta.clear();
 let mode=args.get(3).map(String::as_str).unwrap_or("touch");
 let page=matches!(mode,"home"|"missing"|"settings"|"controls");
 ui::setup(&ctx);
 for frame in 0..4 {
  ctx.begin_pass(egui::RawInput{screen_rect:Some(egui::Rect::from_min_size(egui::Pos2::ZERO,egui::vec2(w,h))),
   safe_area_insets:Some(egui::SafeAreaInsets(egui::epaint::MarginF32{left:12.0,top:10.0,right:12.0,bottom:22.0})),time:Some(frame as f64),..Default::default()});
  if page {ui::draw(&ctx,mode);}else if !controller {t.draw(&ctx.layer_painter(egui::LayerId::background()),0.8);}
  output=ctx.end_pass();output.textures_delta.clear();
 }
 let pad=t.gamepad();'''
    assert old in code;code=code.replace(old,new)
    code=code.replace('"w":w,"h":h,"deck"','"page":if page{mode}else{"game"},"w":w,"h":h,"deck"')
    code=code.replace('map(|s|shape(&s.shape))','map(|s|{let mut v=shape(&s.shape);v["clip"]=json!([s.clip_rect.min.x,s.clip_rect.min.y,s.clip_rect.width(),s.clip_rect.height()]);v})')
    return code
