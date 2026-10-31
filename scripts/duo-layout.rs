//! Original adaptive handheld layout; shared by the native host and its preview/tests.
//! Coordinates are logical points. No device names, screen-size lists or game assets.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Rect { pub x:f32, pub y:f32, pub w:f32, pub h:f32 }
#[derive(Clone, Copy, Debug)]
pub struct Layout { pub game:Rect, pub controls:Rect, pub deck:bool }
#[derive(Clone, Copy, Debug)]
pub struct Circle { pub x:f32, pub y:f32, pub r:f32 }

pub fn layout(w:f32,h:f32,insets:[f32;4],touch:bool)->Layout {
    let w=w.max(1.0); let h=h.max(1.0);
    let [left,top,right,bottom]=insets.map(|v|v.max(0.0));
    let deck=touch && h > w*1.05;
    // A wide, independently rendered game view above a reachable control deck.
    let deck_height=(h*0.42).clamp(280.0,440.0).min(h*0.53);
    let split=if deck { h-deck_height } else { 0.0 };
    Layout { game:Rect{x:0.0,y:0.0,w,h:if deck {split}else{h}},
        controls:Rect{x:left,y:if deck{split+8.0}else{top},
        w:(w-left-right).max(1.0),h:(h-bottom-if deck{split+8.0}else{top}).max(1.0)},deck }
}

/// Portrait layout: 0..11 pad buttons, 12 movement, 13 camera, 14 d-pad, 15 settings.
pub fn deck_control(id:usize,a:Rect,scale:f32)->Circle {
    let s=scale.clamp(0.5,1.5); let spread=(46.0*s).max(36.0);
    let face=(a.x+a.w*0.82,a.y+a.h*0.46);
    let movement=(a.x+a.w*0.20,a.y+a.h*0.44);
    let look=(a.x+a.w*0.58,a.y+a.h*0.78);
    let (x,y,r)=match id {
        0=>(face.0,face.1+spread,25.0*s),
        1=>(face.0+spread,face.1,25.0*s),
        2=>(face.0-spread,face.1,25.0*s),
        3=>(face.0,face.1-spread,25.0*s),
        4=>(a.x+a.w*0.90,a.y+34.0,28.0*s),
        5=>(a.x+a.w*0.73,a.y+34.0,22.0*s),
        6=>(a.x+a.w*0.10,a.y+34.0,28.0*s),
        7=>(a.x+a.w*0.27,a.y+34.0,22.0*s),
        8=>(look.0-92.0*s,look.1,18.0*s),
        9=>(movement.0+92.0*s,movement.1,18.0*s),
        10=>(a.x+a.w*0.50+30.0*s.max(1.0),a.y+a.h*0.28,20.0*s),
        11=>(a.x+a.w*0.50-30.0*s.max(1.0),a.y+a.h*0.28,20.0*s),
        12=>(movement.0,movement.1,56.0*s),
        13=>(look.0,look.1,56.0*s),
        14=>(a.x+a.w*0.17,a.y+a.h*0.82,54.0*s),
        _=>(a.x+a.w*0.50,a.y+34.0,22.0),
    };
    Circle{x,y,r:if id<12 {r.max(22.0)}else{r}}
}

pub fn deck_scale(a:Rect,user:f32)->f32 {
    (user.clamp(0.75,1.25)*(a.w/620.0).min(a.h/340.0).clamp(0.62,1.0))
        .min((a.h*0.36/110.0).max(0.62)).clamp(0.62,1.0)
}

/// Conventional landscape anchors; the portrait deck uses a different arrangement.
pub fn control(id:usize,a:Rect,s:f32,deck:bool)->Circle {
 if deck {return deck_control(id,a,s);}
 let right=a.x+a.w;let bottom=a.y+a.h;let mid=a.x+a.w*0.5;
 let (x,y,r)=match id {
  0=>(right-92.*s,bottom-66.*s,25.),1=>(right-46.*s,bottom-112.*s,25.),
  2=>(right-138.*s,bottom-112.*s,25.),3=>(right-92.*s,bottom-158.*s,25.),
  4=>(right-56.*s,a.y+46.*s,28.),5=>(right-56.*s,a.y+116.*s,22.),
  6=>(a.x+56.*s,a.y+46.*s,28.),7=>(a.x+56.*s,a.y+116.*s,22.),
  8=>(right-304.*s,bottom-150.*s,18.),9=>(a.x+56.*s,bottom-150.*s,18.),
  10=>(mid+34.*s,a.y+30.*s,20.),11=>(mid-34.*s,a.y+30.*s,20.),
  12=>(a.x+150.*s,bottom-156.*s,56.),13=>(right-236.*s,bottom-92.*s,56.),
  14=>(a.x+170.*s,a.y+120.*s,44.),_=>(right-156.*s,a.y+40.*s,22.),
 }; Circle{x,y,r:r*s}
}

#[cfg(any(test,target_arch="wasm32"))]
pub fn geometry_report()->(u32,u32) {
 let mut cases=0;let mut failures=0;
 for (w,h) in [(626.0,890.0),(466.0,678.0),(390.0,844.0)] {
  for user in [0.75,1.0,1.25] {
   cases+=1;let l=layout(w,h,[12.0,10.0,12.0,22.0],true);let s=deck_scale(l.controls,user);
   for i in 0..16 {let c=control(i,l.controls,s,true);
    if i<12 && c.r<22.0 {failures+=1;}
    if c.x-c.r<l.controls.x-0.1 || c.x+c.r>l.controls.x+l.controls.w+0.1 ||
       c.y-c.r<l.controls.y-0.1 || c.y+c.r>l.controls.y+l.controls.h+0.1 {failures+=1;}
    for j in i+1..16 {let other=control(j,l.controls,s,true);
     let d=((c.x-other.x).powi(2)+(c.y-other.y).powi(2)).sqrt();
     if d+0.1<c.r+other.r {failures+=1;}
    }
   }
  }
  cases+=1;let l=layout(h,w,[12.0,10.0,12.0,22.0],true);
  if l.deck || l.game.w!=h || l.game.h!=w {failures+=1;}
  cases+=1;let l=layout(w,h,[12.0,10.0,12.0,22.0],false);
  if l.deck || l.game.w!=w || l.game.h!=h {failures+=1;}
 }
 (cases,failures)
}

#[cfg(test)] mod tests {
 use super::*;
 #[test] fn portrait_geometry_has_no_collisions_at_supported_sizes() {assert_eq!(geometry_report().1,0);}
 #[test] fn landscape_uses_every_pixel_and_portrait_reserves_real_space() {
  for (w,h) in [(890.,626.),(626.,890.),(678.,466.),(466.,678.)] {
   let l=layout(w,h,[12.,10.,12.,22.],true);
   if w>h { assert!(!l.deck);assert_eq!(l.game.w,w);assert_eq!(l.game.h,h); }
   else {assert!(l.deck);assert!(l.controls.y>l.game.h);assert!(l.game.h>=h*0.47);}
   let controller=layout(w,h,[0.;4],false);assert_eq!(controller.game.h,h);assert!(!controller.deck);
  }
 }
 #[test] fn portrait_buttons_fit_and_are_at_least_44_points() {
  for (w,h) in [(626.,890.),(466.,678.),(390.,844.)] {
   let l=layout(w,h,[12.,10.,12.,22.],true);let s=deck_scale(l.controls,1.0);
   for i in 0..16 {let c=deck_control(i,l.controls,s);
    if i<12 {assert!(c.r>=22.);}
    assert!(c.x-c.r>=l.controls.x-1.,"control {i} left");
    assert!(c.x+c.r<=l.controls.x+l.controls.w+1.,"control {i} right");
    assert!(c.y-c.r>=l.controls.y-1.,"control {i} top");
    assert!(c.y+c.r<=l.controls.y+l.controls.h+1.,"control {i} bottom");
   }
  }
 }
 #[test] fn invalid_dimensions_stay_finite() {
  let l=layout(0.,0.,[0.;4],true);assert!(l.game.w.is_finite());assert!(l.game.h>0.);
 }
}
