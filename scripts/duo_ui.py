#!/usr/bin/env python3
"""Original handheld UI/viewport adapter applied only to the ignored upstream clone."""
from pathlib import Path
import shutil
import re

ROOT = Path(__file__).resolve().parents[1]


def replace(path, old, new):
    text = path.read_text()
    if new in text:
        return
    if old == '    fn pos(&self, at: At) -> Pos2 {' and '    fn geometry_area(&self)' in text:
        return
    if text.count(old) != 1:
        raise ValueError('Expected one handheld integration seam: '+str(path)+' '+old[:65])
    path.write_text(text.replace(old,new))


def patch(root):
    app = root/'crates/glue5/src/app.rs'
    ui = root/'crates/glue5/src/ui.rs'
    touch = root/'crates/glue5/src/touch.rs'
    gpu = root/'crates/glue5-gpu/src/present.rs'
    lib = root/'crates/glue5/src/lib.rs'
    ui.write_text(ui.read_text().replace('let a=handheld_layout(window,true).controls;','let a=handheld_layout(window,crate::paths::MOBILE).controls;'))
    # Repair an intermediate adapter version before validating the final helper seam.
    text=touch.read_text().replace('if !self.deck { return self.button_pos(b); }','if !self.deck { return self.pos(b.at); }')
    touch.write_text(text)
    shutil.copyfile(ROOT/'scripts/duo-layout.rs',root/'crates/glue5/src/duo_layout.rs')
    replace(lib, 'mod app;', 'mod app;\nmod duo_layout; // Original adaptive handheld layout')
    replace(app, '"LandscapeLeft LandscapeRight"', '"LandscapeLeft LandscapeRight Portrait PortraitUpsideDown"')
    replace(gpu, '    size: AtomicU64,', '    size: AtomicU64,\n    game_rect: Mutex<Option<[f32;4]>>, // GTA_POC_DUO viewport fractions')
    replace(gpu, '            size: AtomicU64::new(0),', '            size: AtomicU64::new(0),\n            game_rect: Mutex::new(None),')
    replace(gpu, '    pub fn set_vsync(&self, on: bool) {', '''    /// Normalized scene region; the overlay always keeps the whole window.
    pub fn set_game_rect(&self, rect: Option<[f32;4]>) {
        *self.0.game_rect.lock().unwrap_or_else(|e| e.into_inner()) = rect;
    }

    pub fn game_area(&self, size: (u32,u32)) -> (u32,u32,u32,u32) {
        let r = *self.0.game_rect.lock().unwrap_or_else(|e| e.into_inner());
        match r {
            Some([x,y,w,h]) => {
                let px = ((x.clamp(0.0,1.0)*size.0 as f32) as u32).min(size.0.saturating_sub(1));
                let py = ((y.clamp(0.0,1.0)*size.1 as f32) as u32).min(size.1.saturating_sub(1));
                (px,py,((w*size.0 as f32) as u32).max(1).min(size.0.saturating_sub(px).max(1)),
                       ((h*size.1 as f32) as u32).max(1).min(size.1.saturating_sub(py).max(1)))
            }
            None => (0,0,size.0,size.1),
        }
    }

    pub fn game_area_size(&self, size: (u32,u32)) -> (u32,u32) {
        let (_,_,w,h)=self.game_area(size); (w,h)
    }

    pub fn set_vsync(&self, on: bool) {''')
    replace(gpu, '                let rect = fit((p.width, p.height), size);', '''                let area = self.presentation.game_area(size);
                let fitted = fit((p.width, p.height), (area.2,area.3));
                let rect = (area.0+fitted.0,area.1+fitted.1,fitted.2,fitted.3);''')
    replace(ui, 'pub fn safe_rect(window: &Window) -> Rect {', '''/// Scene/deck geometry uses the live window and safe-area insets.
pub fn handheld_layout(window: &Window, touch: bool) -> crate::duo_layout::Layout {
    let (w,h)=window.size();let safe=safe_rect(window);
    crate::duo_layout::layout(w as f32,h as f32,
        [safe.min.x,safe.min.y,w as f32-safe.max.x,h as f32-safe.max.y],touch)
}

pub fn control_rect(window: &Window) -> Rect {
    let a=handheld_layout(window,crate::paths::MOBILE).controls;
    Rect::from_min_size(pos2(a.x,a.y),vec2(a.w,a.h))
}

pub fn safe_rect(window: &Window) -> Rect {''')
    replace(app, 'ui::safe_rect(&self.window), self.settings.touch_size', 'ui::control_rect(&self.window), self.settings.touch_size')
    replace(app, '    fn resize_game(&mut self) {', '''    fn update_game_rect(&self) {
        let touch = MOBILE && match self.settings.touch {
            TouchMode::Always => true, TouchMode::Off => false, TouchMode::Auto => self.touch_input,
        };
        let l=ui::handheld_layout(&self.window,touch);
        let (w,h)=self.window.size();
        self.presentation.set_game_rect(l.deck.then_some([
            l.game.x/w.max(1) as f32,l.game.y/h.max(1) as f32,
            l.game.w/w.max(1) as f32,l.game.h/h.max(1) as f32]));
    }

    fn resize_game(&mut self) {
        self.update_game_rect();''')
    replace(app, 'let size = settings::render_size((w, h), scale, game.started.low_memory);',
            'let size = settings::render_size(self.presentation.game_area_size((w,h)), scale, game.started.low_memory);')
    replace(app, '    fn play(&mut self) -> Result<()> {', '    fn play(&mut self) -> Result<()> {\n        self.update_game_rect();')
    replace(app, 'settings::render_size(self.window.size_in_pixels(), s.render_scale(), s.low_memory)',
            'settings::render_size(self.presentation.game_area_size(self.window.size_in_pixels()), s.render_scale(), s.low_memory)')
    # A new viewport clears held controls even when no physical display size changed.
    replace(touch, '#[derive(Clone, Copy)]\nenum At {', '#[derive(Clone, Copy, PartialEq)]\nenum At {')
    replace(touch, '    scale: f32,\n}', '    scale: f32,\n    deck: bool,\n}')
    replace(touch, 'area, scale: 1.0 }', 'area, scale: 1.0, deck: false }')
    replace(touch, '        self.scale = scale * if phone { PHONE_SCALE } else { 1.0 };', '''        self.deck = screen.y > screen.x*1.05 && area.min.y > screen.y*0.2;
        self.scale = if self.deck { crate::duo_layout::deck_scale(self.geometry_area(),scale) }
            else { scale * if phone { PHONE_SCALE } else { 1.0 } };''')
    replace(touch, '    fn pos(&self, at: At) -> Pos2 {', '''    fn geometry_area(&self) -> crate::duo_layout::Rect {
        crate::duo_layout::Rect{x:self.area.min.x,y:self.area.min.y,w:self.area.width(),h:self.area.height()}
    }
    fn control(&self, id:usize) -> crate::duo_layout::Circle {
        crate::duo_layout::control(id,self.geometry_area(),self.scale,self.deck)
    }
    pub fn gear_position(&self) -> Option<Pos2> {
        self.deck.then(|| {let c=self.control(15);pos2(c.x,c.y)})
    }
    fn button_pos(&self,b:&Button) -> Pos2 {
        let id=BUTTONS.iter().position(|item|item.bits==b.bits).unwrap_or(0);
        let c=self.control(id);pos2(c.x,c.y)
    }
    fn pos(&self, at: At) -> Pos2 {
        for (anchor,id) in [(MOVE_REST,12),(LOOK_REST,13),(DPAD,14)] {
            if at==anchor {let c=self.control(id);return pos2(c.x,c.y);}
        }''')
    # Keep these shared paths consistent across hit testing, drawing and upstream tests.
    text=touch.read_text().replace('self.pos(b.at).distance(p)', 'self.button_pos(b).distance(p)').replace('let c = self.pos(b.at);', 'let c = self.button_pos(b);')
    text=text.replace('(b.radius * self.scale * 1.25).max(22.0)',
        '(b.radius * self.scale * if self.deck {1.0}else{1.25}).max(22.0)')
    text=text.replace('let r = b.radius * self.scale;', 'let r = if self.deck {(b.radius*self.scale).max(22.0)}else{b.radius*self.scale};')
    touch.write_text(text)
    replace(touch, '        let finger = if let Some(i)', '        if self.deck && !self.area.contains(p) { return; }\n        let finger = if let Some(i)')
    replace(touch, '        let alpha = |a: f32|', '''        if self.deck {
            let rect=Rect::from_min_max(pos2(0.0,self.area.min.y-8.0),pos2(self.screen.x,self.screen.y));
            painter.rect_filled(rect,0.0,Color32::from_rgb(19,21,24));
            painter.line_segment([rect.left_top(),rect.right_top()],Stroke::new(1.0,Color32::from_gray(47)));
        }
        let alpha = |a: f32|''')
    replace(ui, 'draw_gear(&ctx, safe, settings.touch_size, alpha)',
            'draw_gear(&ctx, safe, settings.touch_size, alpha, touch.and_then(|t|t.gear_position()))')
    replace(ui, 'fn draw_gear(ctx: &egui::Context, safe: Rect, scale: f32, alpha: f32) -> (Pos2, f32) {',
            'fn draw_gear(ctx: &egui::Context, safe: Rect, scale: f32, alpha: f32, position: Option<Pos2>) -> (Pos2, f32) {')
    replace(ui, 'let c = pos2(safe.max.x + GEAR_AT.x * scale, safe.min.y + GEAR_AT.y * scale);',
            'let c = position.unwrap_or_else(||pos2(safe.max.x + GEAR_AT.x * scale, safe.min.y + GEAR_AT.y * scale));')
    replace(ui, 'const GEAR_RADIUS: f32 = 20.0;', 'const GEAR_RADIUS: f32 = 22.0;')
    replace(touch, '        pad\n    }', '        // A quick trigger tap must publish its analog value for one frame too.\n        if pad.buttons & button::L2 != 0 { pad.l2 = 1.0; }\n        if pad.buttons & button::R2 != 0 { pad.r2 = 1.0; }\n        pad\n    }')
    settings=root/'crates/glue5/src/settings.rs'
    replace(settings, 'max_fps: if MOBILE { 60 } else { 0 },', 'max_fps: if MOBILE { 30 } else { 0 },')
    replace(settings, 'let k = (cap.0 / w).min(cap.1 / h).min(1.0);', '// Bound the scene workload when a mobile display grows; UI stays native resolution.\n    let pixels = if MOBILE && low_memory { (1_500_000.0 / (w*h).max(1.0)).sqrt().min(1.0) } else { 1.0 };\n    let k = (cap.0 / w).min(cap.1 / h).min(1.0).min(pixels);')
    replace(touch, 'let fill = Color32::from_white_alpha(alpha(0.18));',
        'let fill = if self.deck {Color32::from_white_alpha(alpha(0.10))}else{Color32::from_black_alpha(alpha(0.55))};')
    replace(touch, 'let pressed = Color32::from_white_alpha(alpha(0.45));',
        'let pressed = if self.deck {Color32::from_white_alpha(alpha(0.35))}else{Color32::from_black_alpha(alpha(0.80))};')
    replace(touch, 'painter.circle(c, r, if held_button(i) { pressed } else { fill }, stroke);',
        'painter.circle(c, r, if held_button(i) { pressed } else { fill }, if held_button(i) {Stroke::new(2.0*self.scale,Color32::from_rgb(225,190,123))}else{stroke});')
    replace(touch, 'const MOVE_REST: At = At::LeftBottom(150.0, 96.0);',
        'const MOVE_REST: At = At::LeftBottom(150.0, 156.0);')
    replace(touch, '    fn button_pos(&self,b:&Button) -> Pos2 {\n        let id=BUTTONS.iter().position(|item|item.bits==b.bits).unwrap_or(0);\n        let c=self.control(id);pos2(c.x,c.y)\n    }', '    fn button_pos(&self,b:&Button) -> Pos2 {\n        if !self.deck { return self.pos(b.at); }\n        let id=BUTTONS.iter().position(|item|item.bits==b.bits).unwrap_or(0);\n        let c=self.control(id);pos2(c.x,c.y)\n    }\n    fn button_radius(&self,b:&Button) -> f32 {\n        if !self.deck { return b.radius*self.scale; }\n        let id=BUTTONS.iter().position(|item|item.bits==b.bits).unwrap_or(0);\n        self.control(id).r\n    }')
    replace(touch, 'let r = if self.deck {(b.radius*self.scale).max(22.0)}else{b.radius*self.scale};', 'let r = self.button_radius(b);')
    replace(touch, '(b.radius * self.scale * if self.deck {1.0}else{1.25}).max(22.0)', '(self.button_radius(b) * if self.deck {1.0}else{1.25}).max(22.0)')
    replace(app, 'window: self.window.size_in_pixels(),', 'window: self.presentation.game_area_size(self.window.size_in_pixels()),')
    replace(settings, 'assert_eq!(render_size((6016, 3384), 1.0, true), (2560, 1440));', 'assert_eq!(render_size((6016, 3384), 1.0, true), if MOBILE {(1632,918)}else{(2560,1440)});')
    replace(settings, '            touch_opacity: 0.6,', '            touch_opacity: if MOBILE {0.8}else{0.6},')
    replace(settings, '// Phones hold a steady 60 for longer than they hold 120 (heat).', '// Conservative first launch; raise frame rate after a stable session.')
    # Portrait becomes a genuine supported orientation rather than a scaled landscape window.
    project=root/'platform/ios/project.poc.yml'
    text=project.read_text().replace('UIRequiresFullScreen: true','UIRequiresFullScreen: false')
    text=text.replace('[UIInterfaceOrientationLandscapeLeft, UIInterfaceOrientationLandscapeRight]',
        '[UIInterfaceOrientationLandscapeLeft, UIInterfaceOrientationLandscapeRight, UIInterfaceOrientationPortrait, UIInterfaceOrientationPortraitUpsideDown]')
    project.write_text(text)

# Original responsive home page: columns on wide windows, one readable column on narrow ones.
HOME = r'''pub(super) fn start_page(
    ctx: &egui::Context, status: &Status, settings: &mut Settings, starting: bool,
    actions: &mut Vec<Action>, go: &mut Option<Option<Page>>,
) -> bool {
    // GTA_POC_HOME: layout from available space, never from device identity.
    let safe=ctx.content_rect();let width=(safe.width()-32.0).clamp(1.0,1000.0);
    let wide=width>=600.0;let mut play=false;
    egui::Area::new(Id::new("start")).constrain(false)
        .fixed_pos(pos2(safe.center().x-width*0.5,safe.top()+16.0))
        .default_size(vec2(width,(safe.height()-32.0).max(1.0)))
        .show(ctx,|ui| {
            ui.set_width(width);
            egui::ScrollArea::vertical().id_salt("handheld-home")
                .max_height((safe.height()-32.0).max(1.0)).show(ui,|ui| {
                ui.label(theme::heading("GTA V",40.0));
                ui.label(RichText::new("Choose how to play").color(theme::MUTED));
                ui.add_space(18.0);
                if wide {
                    ui.columns(2,|columns| {
                        play=handheld_menu(&mut columns[0],status,settings,starting,actions,go);
                        card(&mut columns[1],|ui|game_files(ui,status));
                        if let Some(why)=status.last_failure {
                            card(&mut columns[1],|ui|last_failure(ui,why,status.graphics_reset,actions));
                        }
                    });
                } else {
                    card(ui,|ui|game_files(ui,status));ui.add_space(12.0);
                    play=handheld_menu(ui,status,settings,starting,actions,go);
                    if let Some(why)=status.last_failure {
                        card(ui,|ui|last_failure(ui,why,status.graphics_reset,actions));
                    }
                }
                ui.add_space(10.0);ui.label(RichText::new(open_hint()).small().color(theme::MUTED));
            });
        });
    play
}

fn handheld_menu(ui:&mut egui::Ui,status:&Status,settings:&mut Settings,starting:bool,
    actions:&mut Vec<Action>,go:&mut Option<Option<Page>>)->bool {
    let width=ui.available_width();let mut play=false;
    ui.add_enabled_ui(status.game_dir.is_some() && !starting,|ui| {
        for (mode,label) in [(1,"Story"),(2,"Playground · GTA V"),(3,"Playground · Test map")] {
            let selected=settings.start_mode==mode;
            let label=RichText::new(label).size(18.0).color(if selected{theme::INK}else{Color32::WHITE});
            if focus(ui.add_sized([width,48.0],egui::Button::new(label)
                .fill(if selected{Color32::from_rgb(225,190,123)}else{Color32::from_gray(35)})
                .corner_radius(10))).clicked() {settings.start_mode=mode;}
            ui.add_space(4.0);
        }
        ui.add_space(8.0);
        play=menu_button(ui,width,if starting{"Starting…"}else{"Play"},true).clicked();
    });
    if menu_button(ui,width,"Settings",false).clicked(){*go=Some(Some(Page::Settings));}
    if menu_button(ui,width,if MOBILE{"Find game files"}else{"Game folder"},false).clicked(){
        actions.push(if MOBILE{Action::FindGame}else{Action::ChooseGame});
    }
    if !MOBILE && menu_button(ui,width,"Quit",false).clicked(){actions.push(Action::Quit);}
    play
}

'''


def patch_home(root):
    page=root/'crates/glue5/src/ui/pages.rs'
    text=page.read_text()
    a=text.index('pub(super) fn start_page(')
    b=text.index('fn menu_button(',a)
    text=text[:a]+HOME+text[b:]
    text=text.replace('start_page(root.ctx(), &status(), false,', 'start_page(root.ctx(), &status(), &mut Settings::default(), false,')
    text=text.replace('d.display().to_string());', 'if MOBILE {"On this device".to_owned()}else{d.display().to_string()});')
    page.write_text(text)

TOUCH_TESTS = r'''
#[cfg(test)]
mod gta_poc_touch_tests {
    use super::*;
    fn portrait(w:f32,h:f32)->Touch {
        let l=crate::duo_layout::layout(w,h,[12.0,10.0,12.0,22.0],true);
        let mut t=Touch::new();t.layout(vec2(w,h),Rect::from_min_size(pos2(l.controls.x,l.controls.y),vec2(l.controls.w,l.controls.h)),1.0);t
    }
    fn down(t:&mut Touch,finger:u64,id:usize) {
        let c=t.control(id);t.finger_down(finger,c.x/t.screen.x,c.y/t.screen.y);
    }
    #[test] fn simultaneous_move_camera_and_action_work() {
        let mut t=portrait(626.0,890.0);down(&mut t,1,12);let m=t.control(12);
        t.finger_motion(1,(m.x+t.stick_radius()*0.5)/t.screen.x,m.y/t.screen.y);
        down(&mut t,2,13);let c=t.control(13);
        t.finger_motion(2,(c.x-t.stick_radius()*0.5)/t.screen.x,c.y/t.screen.y);
        down(&mut t,3,0);let p=t.gamepad();
        assert!((p.left[0]-0.5).abs()<0.001);assert!((p.right[0]+0.5).abs()<0.001);
        assert_ne!(p.buttons & button::SOUTH,0);
        t.clear();let p=t.gamepad();assert_eq!(p.left,[0.0;2]);assert_eq!(p.right,[0.0;2]);assert_eq!(p.buttons,0);
    }
    #[test] fn quick_trigger_tap_has_one_frame_of_analog_value() {
        let mut t=portrait(626.0,890.0);down(&mut t,1,4);t.finger_up(1);
        assert_eq!(t.gamepad().r2,1.0);assert_eq!(t.gamepad().r2,0.0);
    }
    #[test] fn scene_touches_do_not_start_a_stick_and_layout_changes_release_input() {
        let mut t=portrait(626.0,890.0);t.finger_down(1,0.2,0.2);
        assert!(t.fingers.is_empty());down(&mut t,2,0);assert!(!t.fingers.is_empty());
        t.layout(vec2(890.0,626.0),Rect::from_min_size(pos2(12.0,10.0),vec2(866.0,594.0)),1.0);
        assert!(t.fingers.is_empty());assert_eq!(t.gamepad().buttons,0);
    }
    #[test] fn portrait_buttons_fit_do_not_overlap_and_have_44_point_targets() {
        for (w,h) in [(626.0,890.0),(466.0,678.0),(390.0,844.0)] {
            let t=portrait(w,h);
            for (i,b) in BUTTONS.iter().enumerate() {
                let c=t.button_pos(b);let r=(b.radius*t.scale).max(22.0);
                assert!(t.area.contains_rect(Rect::from_center_size(c,Vec2::splat(r*2.0))),"{i} leaves deck");
                for other in &BUTTONS[i+1..] {
                    let q=t.button_pos(other);let qr=(other.radius*t.scale).max(22.0);
                    assert!(c.distance(q)>=r+qr,"buttons overlap: {i}");
                }
            }
        }
    }
}
'''


def patch_input_safety(root):
    path=root/'crates/glue5/src/touch.rs'
    replace(path,'        self.screen = screen;',
        '        if self.screen != screen || self.area != area { self.clear(); }\n        self.screen = screen;')
    text=path.read_text()
    if 'mod gta_poc_touch_tests' not in text:path.write_text(text+TOUCH_TESTS)


def patch_settings_targets(root):
    """Keep settings legible on the open display and targets large in compact views."""
    theme=root/'crates/glue5/src/ui/theme.rs'
    replace(theme,'rect.width() / 780.0','rect.width() / 560.0')
    widgets=root/'crates/glue5/src/ui/widgets.rs'
    text=widgets.read_text().replace('1(88.0 + 4.0 * scale)','180.0 * scale')
    widgets.write_text(text)
    if 'GTA_POC_SETTINGS_TOUCH' not in text:
        if text.count('44.0 * scale')<4:raise ValueError('Missing settings target seams')
        text=text.replace('44.0 * scale','(44.0 * scale).max(44.0)')
        text=text.replace('38.0 * scale','44.0')
        text=re.sub(r'(?<![\d.])80\.0 \* scale','(88.0 + 4.0 * scale)',text)
        text=text.replace('40.0 * scale','(40.0 * scale).max(44.0)')
        widgets.write_text(text+'\n// GTA_POC_SETTINGS_TOUCH: targets remain at least 44 points.\n')
    replace(widgets, '.min_size(vec2(0.0, (40.0 * scale).max(44.0)))', '.min_size(vec2(44.0, (40.0 * scale).max(44.0)))')
    pages=root/'crates/glue5/src/ui/pages.rs'
    text=pages.read_text()
    if 'GTA_POC_SETTINGS_TABS' not in text:
        text=text.replace('40.0 * scale','(40.0 * scale).max(44.0)')
        pages.write_text(text+'\n// GTA_POC_SETTINGS_TABS: minimum 44-point tab targets.\n')


def patch_settings_scroll_tests(root):
    """Update private compact-screen assertions for larger, reachable touch targets."""
    page=root/'crates/glue5/src/ui/pages.rs'
    replace(page,'        let mut tab = SettingsTab::Video;\n        for pass in 0..8 {',
        '        let mut seen_options=std::collections::HashSet::new();\n        let mut tab = SettingsTab::Video;\n        for pass in 0..8 {')
    replace(page,'            output.textures_delta.clear();\n            if pass == 3 || pass == 7 {',
        '            output.textures_delta.clear();\n            for primitive in &output.shapes {\n                if let egui::Shape::Text(t)=&primitive.shape {seen_options.insert(t.galley.job.text.clone());}\n            }\n            if pass == 3 || pass == 7 {')
    replace(page,'assert_eq!(rows.len(), if cfg!(target_vendor = "apple") { 5 } else { 4 });',
        'assert!(rows.len() >= 3, "compact settings lost its visible options");')
    replace(page,'let visible = if pass == 3 { &rows[..4] } else { &rows[rows.len() - 1..] };',
        'let visible = if pass == 3 { &rows[..3] } else { &rows[rows.len() - 1..] };')
    replace(page,'        assert!(safe.height() - window.height() <= 12.0, "wasted height: {window:?} in {safe:?}");',
        '        assert!(safe.height() - window.height() <= 12.0, "wasted height: {window:?} in {safe:?}");\n        for label in ["Resolution","Upscaling","Frame rate","VSync"] {assert!(seen_options.contains(label),"unreachable option: {label}");}\n        if cfg!(target_vendor="apple") {assert!(seen_options.contains("Metal HUD"));}')

SETTINGS_TARGET_TESTS = r'''
#[cfg(test)]
mod gta_poc_settings_targets {
 use super::*;
 #[test] fn compact_and_open_settings_keep_44_point_targets() {
  for scale in [0.75,1.0] {
   let ctx=egui::Context::default();crate::ui::theme::install(&ctx);
   let mut rects=Vec::new();let mut value=0.5;let mut toggle_value=true;let mut selected=0;
   let mut output=ctx.run_ui(egui::RawInput{screen_rect:Some(Rect::from_min_size(Pos2::ZERO,vec2(626.0,890.0))),..Default::default()},|ui| {
    crate::ui::theme::apply_density(ui,scale);ui.set_width(500.0);ui.spacing_mut().slider_width=120.0;
    rects.push(close_button(ui).rect);rects.push(toggle(ui,&mut toggle_value).rect);
    rects.push(slider(ui,&mut value,0.0..=1.0,0.1,"%",0).rect);
    rects.push(choice(ui,&mut selected,&[(0,"First"),(1,"Second")]).rect);
    rects.push(action_button(ui,"Open").rect);
   });output.textures_delta.clear();
   for rect in rects {assert!(rect.width()>=44.0 && rect.height()>=44.0,"small target at {scale}: {rect:?}");}
  }
 }
}
'''


def add_settings_target_tests(root):
    path=root/'crates/glue5/src/ui/widgets.rs';text=path.read_text()
    if 'mod gta_poc_settings_targets' not in text:path.write_text(text+SETTINGS_TARGET_TESTS)
