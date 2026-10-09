# -*- coding: utf-8 -*-
"""节点图前端渲染：把 Houdini 节点网络还原成网页可交互节点图"""
import json


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


CSS = """
*{box-sizing:border-box}
body{margin:0;background:#1c1f26;color:#d8dee9;
font:13px/1.6 "Segoe UI","Microsoft YaHei",sans-serif;overflow:hidden}
#top{position:fixed;left:0;right:0;top:0;height:44px;background:#12141a;
border-bottom:1px solid #2a2f39;display:flex;align-items:center;padding:0 14px;z-index:60;gap:10px}
#top b{color:#6cb6ff;font-size:14px}
#bc{display:flex;align-items:center;gap:5px;font-size:12px;color:#8a95a5;flex-wrap:wrap}
#bc a{color:#6cb6ff;text-decoration:none;cursor:pointer}
#bc a:hover{text-decoration:underline}
#bc span.sep{color:#4a515c}
#topbtn{margin-left:auto;display:inline-flex;align-items:center;gap:5px;padding:4px 11px;background:#22384d;color:#6cb6ff;border:1px solid #2f4d68;border-radius:4px;font-size:12px;text-decoration:none;cursor:pointer;white-space:nowrap}
#topbtn:hover{background:#2b4661;color:#8ec8ff}
#tip{margin-left:auto;font-size:11px;color:#6d7684}
#main{position:fixed;left:0;right:0;top:44px;bottom:0;display:flex;align-items:stretch}
#left{width:430px;min-width:240px;max-width:75%;display:flex;flex-direction:column;
background:#161920;border-right:1px solid #2a2f39}
#shotpane{height:300px;min-height:0;flex:none;position:relative;background:#0f1115;
border-bottom:1px solid #2a2f39;display:flex;align-items:center;justify-content:center;overflow:hidden}
#shotpane img{max-width:100%;max-height:100%;object-fit:contain;cursor:zoom-in;display:block}
#shotpane .ph{color:#4a515c;font-size:12px;text-align:center;padding:0 20px}
#shotcap{position:absolute;left:0;right:0;bottom:0;background:rgba(15,17,21,.82);
color:#8a95a5;font-size:10.5px;padding:3px 8px;pointer-events:none}
#hsplit{height:6px;flex:none;background:#1c1f26;cursor:row-resize;position:relative}
#hsplit:hover,#hsplit.on{background:#6cb6ff}
#hsplit::after{content:'';position:absolute;left:50%;top:2px;width:34px;height:2px;
margin-left:-17px;background:#3d4450;border-radius:2px}
#vsplit{width:6px;flex:none;background:#1c1f26;cursor:col-resize;position:relative;z-index:56}
#vsplit:hover,#vsplit.on{background:#6cb6ff}
#vsplit::after{content:'';position:absolute;top:50%;left:2px;height:34px;width:2px;
margin-top:-17px;background:#3d4450;border-radius:2px}
#wrap{flex:1;min-width:0;position:relative;overflow:hidden;background:#1c1f26;
background-image:radial-gradient(#282d36 1px,transparent 1px);background-size:26px 26px}
svg{width:100%;height:100%;cursor:grab;display:block}
svg.drag{cursor:grabbing}
.nd rect.bd{fill:#3d4450;stroke:#11131a;stroke-width:1.4;rx:3}
.nd:hover rect.bd{stroke:#6cb6ff;stroke-width:2}
.nd.sel rect.bd{stroke:#ffb454;stroke-width:2.6}
.nd text.nm{fill:#e6ebf2;font-size:11px;dominant-baseline:middle;pointer-events:none}
.nd text.tp{fill:#8a95a5;font-size:8.5px;dominant-baseline:middle;pointer-events:none}
.nd .flag{fill:#2ecc71}
.nd .flagr{fill:#4da3ff}
.nd .cont{fill:#c792ea}
.nd .err{fill:#ff6b6b}
.nd .warn{fill:#ffb454}
.ed{stroke:#7c8797;stroke-width:1.6;fill:none}
.ed.hl{stroke:#6cb6ff;stroke-width:2.6}
.port{fill:#8f9aab}
.loopbox{fill:rgba(255,196,84,.07);stroke:#8a6d2f;stroke-dasharray:5 4;rx:8}
.loopbox-t{fill:#ffc454;font-size:11px}
.nd.blk .bd{stroke:#ffc454;stroke-width:2}
.nd.isin .bd{stroke:#4a5768;stroke-dasharray:4 3}
.b-blk{background:#4a3a17;color:#ffc454}
#side{flex:1;min-height:0;background:#161920;overflow-y:auto;padding:16px}
#side h2{margin:0 0 3px;font-size:15px;color:#6cb6ff;word-break:break-all}
#side .pth{font-size:11px;color:#6d7684;word-break:break-all;margin-bottom:12px}
.bdg{display:inline-block;padding:1px 7px;border-radius:9px;font-size:10.5px;margin:0 5px 5px 0}
.b-sub{background:#22384d;color:#6cb6ff}
.b-loop{background:#3a2b4d;color:#c792ea}
.b-fl{background:#1f3d2b;color:#a3d977}
.b-er{background:#4a2222;color:#ff6b6b}
.sec{margin:13px 0 0;border-top:1px solid #262b34;padding-top:11px}
.sec h3{margin:0 0 7px;font-size:11.5px;color:#8a95a5;text-transform:uppercase;letter-spacing:.6px}
.kv{display:flex;font-size:12px;margin-bottom:4px}
.kv .k{color:#8a95a5;width:96px;flex-shrink:0}
.kv .v{color:#d8dee9;word-break:break-all}
pre{background:#0f1115;border:1px solid #262b34;border-radius:5px;padding:9px;
font:11.5px/1.55 Consolas,monospace;color:#a3d977;overflow-x:auto;margin:0;white-space:pre-wrap}
.fn{font-size:12.5px;color:#c8d0da;line-height:1.65}
.kv .v.hi{color:#a3d977;font-weight:600}
.src{background:#1b1f27;border:1px solid #262b34;border-radius:5px;padding:7px 9px;
margin-bottom:6px;cursor:pointer;font-size:12px}
.src:hover{border-color:#6cb6ff;background:#1f2632}
.src b{color:#e6ebf2}
.src i{color:#8a95a5;font-style:normal;font-size:11px}
.src .pi{display:inline-block;background:#22384d;color:#6cb6ff;border-radius:3px;
padding:0 6px;font-size:10px;margin-right:6px}
.src .sm{color:#a3d977;font-size:11px;margin-top:3px}
.none{color:#6d7684;font-size:12px}
.atl{font-size:11.5px;margin-top:5px;line-height:1.6;word-break:break-all}
.atl.add{color:#a3d977}
.atl.del{color:#ff8f8f}
.atl.mod{color:#ffb454}
.fold{margin-top:5px}
.fold summary{color:#ff8f8f;font-size:11.5px;cursor:pointer;outline:none}
.fold summary:hover{color:#ffb0b0}
.fold .atl{margin-top:4px}
.atl sub{color:#6d7684;font-size:9px}
.pit{font-size:12px;color:#ffb454;line-height:1.65;background:#2a2318;
border-left:3px solid #ffb454;padding:7px 9px;border-radius:3px}
#side img{width:100%;border:1px solid #262b34;border-radius:5px;margin-top:6px;cursor:zoom-in}
.enter{display:inline-block;margin-top:9px;padding:5px 13px;background:#22384d;color:#6cb6ff;
border-radius:4px;font-size:12px;cursor:pointer;border:1px solid #2f4d68}
.enter:hover{background:#2b4661}
.empty{color:#6d7684;font-size:12.5px;margin-top:34px;text-align:center}
#ov{position:fixed;inset:0;background:rgba(0,0,0,.9);z-index:99;display:none;
align-items:center;justify-content:center;cursor:zoom-out}
#ov img{max-width:94%;max-height:94%}
#mini{position:fixed;right:14px;bottom:10px;font-size:11px;color:#5c646f;z-index:55;pointer-events:none}
"""


JS = """
var G=DATA.graphs, CUR=DATA.root, SEL=null, STK=[];
var vb={x:0,y:0,s:1};
var svg=document.getElementById('g'), root=document.getElementById('gr');
var NW=140,NH=34,SX=1.55,SY=1.05;

function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}

function layout(g){
  var ns=g.nodes; if(!ns.length) return {w:0,h:0};
  var minx=1e9,miny=1e9,maxx=-1e9,maxy=-1e9;
  ns.forEach(function(n){
    n.sx=n.x*NW*SX/1.4; n.sy=-n.y*NH*SY*1.4;
    if(n.sx<minx)minx=n.sx; if(n.sy<miny)miny=n.sy;
    if(n.sx>maxx)maxx=n.sx; if(n.sy>maxy)maxy=n.sy;
  });
  ns.forEach(function(n){n.sx-=minx-60; n.sy-=miny-60;});
  return {w:maxx-minx+NW+120,h:maxy-miny+NH+120};
}

function draw(){
  var g=G[CUR]; if(!g){root.innerHTML='';return;}
  layout(g);
  var h='';
  // 循环分组底框
  var loops={};
  g.nodes.forEach(function(n){ if(n.loop){ (loops[n.loop]=loops[n.loop]||[]).push(n); } });
  Object.keys(loops).forEach(function(k){
    var a=loops[k],x1=1e9,y1=1e9,x2=-1e9,y2=-1e9;
    a.forEach(function(n){x1=Math.min(x1,n.sx);y1=Math.min(y1,n.sy);
      x2=Math.max(x2,n.sx+NW);y2=Math.max(y2,n.sy+NH);});
    h+='<rect class="loopbox" x="'+(x1-16)+'" y="'+(y1-30)+'" width="'+(x2-x1+32)+
       '" height="'+(y2-y1+46)+'"/>'+
       '<text class="loopbox-t" x="'+(x1-10)+'" y="'+(y1-14)+'">loop: '+esc(k)+'</text>';
  });
  // 连线
  g.edges.forEach(function(e){
    var a=g.nodes[e.f],b=g.nodes[e.t]; if(!a||!b) return;
    var x1=a.sx+NW/2, y1=a.sy+NH, x2=b.sx+12+e.i*15, y2=b.sy;
    var my=(y1+y2)/2;
    h+='<path class="ed" data-f="'+e.f+'" data-t="'+e.t+'" d="M'+x1+' '+y1+
       ' C'+x1+' '+my+' '+x2+' '+my+' '+x2+' '+y2+'"/>';
  });
  // 节点
  g.nodes.forEach(function(n,i){
    var cls='nd'+(SEL===n.p?' sel':'')+(n.blk?' blk':'')+(n.isin?' isin':'');
    h+='<g class="'+cls+'" data-i="'+i+'" transform="translate('+n.sx+','+n.sy+')">';
    h+='<rect class="bd" width="'+NW+'" height="'+NH+'" fill="'+n.c+'"/>';
    h+='<rect x="0" y="0" width="5" height="'+NH+'" fill="'+(n.blk?'#ffc454':(n.isin?'#4a5768':(n.k?'#c792ea':'#6cb6ff')))+'" rx="2"/>';
    h+='<text class="nm" x="12" y="13">'+esc(n.n)+'</text>';
    h+='<text class="tp" x="12" y="25">'+esc(n.t)+'</text>';
    // 输入端口
    if(!n.isin){ for(var k=0;k<4;k++){ h+='<rect class="port" x="'+(8+k*15)+'" y="-3" width="9" height="3.4" rx="1"/>'; } }
    h+='<rect class="port" x="'+(NW/2-5)+'" y="'+NH+'" width="10" height="3.4" rx="1"/>';
    if(n.fl.indexOf('display')>=0) h+='<circle class="flag" cx="'+(NW-11)+'" cy="11" r="4"/>';
    if(n.fl.indexOf('render')>=0) h+='<circle class="flagr" cx="'+(NW-11)+'" cy="24" r="4"/>';
    if(n.nk>0) h+='<text class="cont" x="'+(NW-30)+'" y="27" font-size="9">['+n.nk+']</text>';
    if(n.er==='error') h+='<circle class="err" cx="'+(NW-11)+'" cy="11" r="4"/>';
    else if(n.er==='warn') h+='<circle class="warn" cx="'+(NW-11)+'" cy="11" r="4"/>';
    h+='</g>';
  });
  root.innerHTML=h;
  bind(g);
  crumbs();
}

function bind(g){
  root.querySelectorAll('.nd').forEach(function(el){
    el.addEventListener('click',function(ev){
      ev.stopPropagation();
      var n=g.nodes[+el.dataset.i]; SEL=n.p; draw(); show(n);
    });
    el.addEventListener('dblclick',function(ev){
      ev.stopPropagation();
      var n=g.nodes[+el.dataset.i];
      if(G[n.p]){ STK.push(CUR); CUR=n.p; fit(); draw(); }
    });
    el.addEventListener('mouseenter',function(){
      var i=+el.dataset.i;
      root.querySelectorAll('.ed').forEach(function(p){
        if(+p.dataset.f===i||+p.dataset.t===i) p.classList.add('hl');
      });
    });
    el.addEventListener('mouseleave',function(){
      root.querySelectorAll('.ed.hl').forEach(function(p){p.classList.remove('hl');});
    });
  });
}

function show(n){
  var s=document.getElementById('side'),h='';
  h+='<h2>'+esc(n.n)+'</h2><div class="pth">'+esc(n.p)+'</div>';
  if(n.no) h+='<span class="bdg b-sub">\u6267\u884c\u5e8f '+esc(n.no)+'</span>';
  if(n.k) h+='<span class="bdg b-sub">'+esc(n.k)+' '+n.nk+'\u8282\u70b9</span>';
  if(n.loop) h+='<span class="bdg b-loop">loop '+esc(n.loop)+'</span>';
  if(n.blk) h+='<span class="bdg b-blk">BLOCK</span>';
  (n.fl||[]).forEach(function(f){h+='<span class="bdg b-fl">'+f+'</span>';});
  if(n.er) h+='<span class="bdg b-er">'+n.er+'</span>';

  h+='<div class="sec"><h3>\u8282\u70b9\u529f\u80fd</h3><div class="fn">'+esc(n.desc||(n.t+' \u8282\u70b9'))+'</div></div>';

  h+='<div class="sec"><h3>\u57fa\u672c\u4fe1\u606f</h3>';
  h+='<div class="kv"><div class="k">\u8282\u70b9\u7c7b\u578b</div><div class="v">'+esc(n.t)+'</div></div>';
  h+='<div class="kv"><div class="k">\u56fe\u5185\u5750\u6807</div><div class="v">'+n.x.toFixed(2)+', '+n.y.toFixed(2)+'</div></div>';
  if(n.st){
    h+='<div class="kv"><div class="k">\u70b9\u6570</div><div class="v hi">'+n.st.pts+'</div></div>';
    h+='<div class="kv"><div class="k">\u9762\u6570</div><div class="v hi">'+n.st.prims+'</div></div>';
  }else{
    h+='<div class="kv"><div class="k">\u51e0\u4f55\u8f93\u51fa</div><div class="v">\u65e0</div></div>';
  }

  // \u4f9d\u8d56\u5c5e\u6027
  h+='<div class="sec"><h3>\u8f93\u5165\u4f9d\u8d56\u7684\u5c5e\u6027</h3>';
  h+='<div class="fn">'+esc(n.reads||'\u65e0\uff08\u4e0d\u8bfb\u53d6\u5c5e\u6027\uff09')+'</div></div>';

  // \u8f93\u51fa\u5c5e\u6027\uff08\u4ec5\u589e\u91cf\uff09
  h+='<div class="sec"><h3>\u8f93\u51fa\u5c5e\u6027\u53d8\u5316</h3>';
  (function(){
    var inA={};
    (n.srcs||[]).forEach(function(sc){
      if(!sc.st) return;
      ['pt_attrs','pr_attrs','det_attrs','vtx_attrs'].forEach(function(kk){
        (sc.st[kk]||[]).forEach(function(a){ inA[a]=1; });
      });
    });
    var added=[],mod=[],seen={};
    (n.newa||[]).forEach(function(a){
      var nm=String(a).split(' ')[0];
      if(seen[nm]) return; seen[nm]=1; added.push(a);
    });
    if(n.writes){
      String(n.writes).split(/[\u3001,\uff0c]/).forEach(function(w){
        var nm=w.trim(); if(!nm||seen[nm]) return; seen[nm]=1;
        if(inA[nm]) mod.push(nm); else added.push(nm);
      });
    }
    var gone=[],gs={};
    (n.gonea||[]).forEach(function(a){ if(!gs[a]){gs[a]=1;gone.push(a);} });
    if(!added.length&&!mod.length&&!gone.length){
      h+='<div class="none">\u65e0\u5c5e\u6027\u53d8\u5316\uff08\u4ec5\u51e0\u4f55/\u62d3\u6251\u5904\u7406\uff09</div>';
    }
    if(added.length) h+='<div class="atl add">+ \u65b0\u589e '+added.join(' , ')+'</div>';
    if(mod.length)   h+='<div class="atl mod">~ \u4fee\u6539 '+esc(mod.join(' , '))+'</div>';
    if(gone.length){
      if(gone.length<=12){
        h+='<div class="atl del">- \u6e05\u9664 '+esc(gone.join(' , '))+'</div>';
      }else{
        h+='<details class="fold"><summary>- \u6e05\u9664 '+gone.length+' \u9879\u5c5e\u6027\uff08\u70b9\u51fb\u5c55\u5f00\uff09</summary>'+
           '<div class="atl del">'+esc(gone.join(' , '))+'</div></details>';
      }
    }
  })();
  h+='</div>';

  // \u8f93\u5165\u6e90
  h+='<div class="sec"><h3>\u8f93\u5165\u6e90</h3>';
  if(n.srcs&&n.srcs.length){
    n.srcs.forEach(function(sc){
      var cnt=sc.st?(sc.st.pts+' \u70b9 / '+sc.st.prims+' \u9762'):'\u65e0\u51e0\u4f55';
      h+='<div class="src" onclick="jump(\\''+sc.p+'\\')"><span class="pi">\u8f93\u5165'+sc.i+'</span>'+
         '<b>'+esc(sc.n)+'</b> <i>'+esc(sc.t)+'</i><div class="sm">'+cnt+'</div></div>';
    });
  }else{ h+='<div class="none">\u65e0\u8f93\u5165\uff08\u751f\u6210\u5668/\u6e90\u5934\u8282\u70b9\uff09</div>'; }
  h+='</div>';

  if(n.pit){ h+='<div class="sec"><h3>\u53ef\u80fd\u7684\u5751\u70b9</h3><div class="pit">'+esc(n.pit)+'</div></div>'; }

  var g=G[CUR],me=g.nodes.indexOf(n),outs=[];
  g.edges.forEach(function(e){ if(e.f===me) outs.push(g.nodes[e.t].n); });
  h+='<div class="sec"><h3>\u4e0b\u6e38\u8282\u70b9</h3><div class="fn">'+
     (outs.length?esc(outs.join(', ')):'\u65e0\uff08\u94fe\u672b\u7aef\uff09')+'</div></div>';

  if(n.parms&&n.parms.length){
    h+='<div class="sec"><h3>\u5df2\u4fee\u6539\u53c2\u6570</h3>';
    n.parms.forEach(function(pm){
      h+='<div class="kv"><div class="k">'+esc(pm.n)+'</div><div class="v">'+esc(pm.v)+'</div></div>';
    });
    h+='</div>';
  }

  if(n.vex){ h+='<div class="sec"><h3>VEX / \u4ee3\u7801</h3><pre>'+esc(n.vex)+'</pre></div>'; }
  // 截图已移至左上固定面板 #shotpane
  if(G[n.p]) h+='<div class="enter" onclick="into(\\''+n.p+'\\')">\u8fdb\u5165\u5185\u90e8\u7f51\u7edc \u25b8</div>';
  s.innerHTML=h;
  setShot(n);
  s.scrollTop=0;
}

function setShot(n){
  var sp=document.getElementById('shotpane');
  if(n&&n.shot){
    sp.innerHTML='<img src="'+n.shot+'" onclick="zoom(this.src)"/>'+
      '<div id="shotcap">'+esc(n.n)+' · '+esc(n.t)+
      (n.st?(' · '+n.st.pts+' 点 / '+n.st.prims+' 面'):'')+'</div>';
  }else{
    sp.innerHTML='<div class="ph">'+(n?esc(n.n)+'<br>该环节无视口截图':'选中节点后<br>此处显示该环节视口截图')+'</div>';
  }
}

function jump(path){
  var g=G[CUR];
  for(var i=0;i<g.nodes.length;i++){
    if(g.nodes[i].p===path){ SEL=path; draw(); show(g.nodes[i]); return; }
  }
}

function into(p){ if(G[p]){ STK.push(CUR); CUR=p; fit(); draw(); } }
function up(){ if(STK.length){ CUR=STK.pop(); fit(); draw(); } }
function goto_(p){ var i=STK.indexOf(p); if(i>=0){ STK=STK.slice(0,i); } CUR=p; fit(); draw(); }

function crumbs(){
  var b=document.getElementById('bc'),h='';
  STK.concat([CUR]).forEach(function(p,i,a){
    var g=G[p]; var nm=g?g.name:p;
    if(i<a.length-1) h+='<a onclick="goto_(\\''+p+'\\')">'+esc(nm)+'</a><span class="sep">/</span>';
    else h+='<b style="color:#d8dee9;font-weight:600">'+esc(nm)+'</b>';
  });
  var g=G[CUR];
  if(g) h+='<span class="sep">·</span><span>'+g.nodes.length+' 节点</span>';
  b.innerHTML=h;
}

function apply(){ root.setAttribute('transform','translate('+vb.x+','+vb.y+') scale('+vb.s+')'); }
function fit(){
  var g=G[CUR]; if(!g||!g.nodes.length) return;
  var d=layout(g), w=svg.clientWidth, h=svg.clientHeight;
  if(!w||w<=0){ var r=svg.getBoundingClientRect(); w=r.width||(window.innerWidth-390); }
  if(!h||h<=0){ var r2=svg.getBoundingClientRect(); h=r2.height||(window.innerHeight-44); }
  vb.s=Math.min(w/(d.w+80), h/(d.h+80), 1.3); if(!isFinite(vb.s)||vb.s<=0) vb.s=1;
  vb.x=(w-d.w*vb.s)/2; vb.y=(h-d.h*vb.s)/2; apply();
}
var dg=false,lx=0,ly=0;
svg.addEventListener('mousedown',function(e){dg=true;lx=e.clientX;ly=e.clientY;svg.classList.add('drag');});
window.addEventListener('mouseup',function(){dg=false;svg.classList.remove('drag');});
window.addEventListener('mousemove',function(e){
  if(!dg)return; vb.x+=e.clientX-lx; vb.y+=e.clientY-ly; lx=e.clientX; ly=e.clientY; apply();});
svg.addEventListener('wheel',function(e){
  e.preventDefault();
  var r=svg.getBoundingClientRect(), mx=e.clientX-r.left, my=e.clientY-r.top;
  var f=e.deltaY<0?1.12:1/1.12, ns=Math.max(.12,Math.min(3.5,vb.s*f));
  vb.x=mx-(mx-vb.x)*(ns/vb.s); vb.y=my-(my-vb.y)*(ns/vb.s); vb.s=ns; apply();},{passive:false});
svg.addEventListener('click',function(){SEL=null;draw();
  document.getElementById('side').innerHTML='<div class="empty">点击任意节点查看详情<br>双击带 [n] 标记的节点进入内部</div>';});
window.addEventListener('keydown',function(e){
  if(e.key==='Escape') up();
  if(e.key==='f'||e.key==='F') fit();
});
function zoom(src){var o=document.getElementById('ov');o.style.display='flex';
  o.querySelector('img').src=src;}
document.getElementById('ov').addEventListener('click',function(){this.style.display='none';});

/* ---------- 可拖拽分割线 ---------- */
(function(){
  var L=document.getElementById('left'), SP=document.getElementById('shotpane');
  var V=document.getElementById('vsplit'), H=document.getElementById('hsplit');
  var MIN_L=240, MIN_SHOT=80, MIN_SIDE=120;
  function noSel(on){ document.body.style.userSelect=on?'none':''; }
  var vOn=false, hOn=false;
  V.addEventListener('mousedown',function(e){ vOn=true; V.classList.add('on'); noSel(true); e.preventDefault(); });
  H.addEventListener('mousedown',function(e){ hOn=true; H.classList.add('on'); noSel(true); e.preventDefault(); });
  window.addEventListener('mousemove',function(e){
    if(vOn){
      var w=e.clientX, max=window.innerWidth*0.8;
      if(w<MIN_L) w=MIN_L; if(w>max) w=max;
      L.style.width=w+'px'; fit();
    }
    if(hOn){
      var lr=L.getBoundingClientRect();
      var hgt=e.clientY-lr.top, maxh=lr.height-MIN_SIDE;
      if(hgt<MIN_SHOT) hgt=MIN_SHOT; if(hgt>maxh) hgt=maxh;
      SP.style.height=hgt+'px';
    }
  });
  window.addEventListener('mouseup',function(){
    if(vOn||hOn){ noSel(false); fit(); }
    vOn=false; hOn=false;
    V.classList.remove('on'); H.classList.remove('on');
  });
})();
draw();requestAnimationFrame(function(){fit();});window.addEventListener('resize',function(){fit();});
document.getElementById('side').innerHTML='<div class="empty">点击任意节点查看详情<br>双击带 [n] 标记的节点进入内部</div>';
"""


def build(root_path, items, shots, graphs, meta):
    data = {"root": root_path, "graphs": graphs}
    return (
        '<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">'
        '<title>' + _esc(meta.get("name", "")) + ' 节点图</title>'
        '<style>' + CSS + '</style></head><body>'
        '<div id="top"><b>' + _esc(meta.get("name", "")) + '</b>'
        '<div id="bc"></div>'
        '<div id="tip">滚轮缩放 · 拖拽平移 · 单击看详情 · 双击进子网 · F 复位 · Esc 返回上层</div>'
        '<a id="topbtn" href="pipeline.html" title="切换到三级目录长文档版（含截图灯箱与 ←→ 翻页对比）">\u2630 \u6587\u6863\u7248\u62a5\u544a</a></div>'
        '<div id="main">'
        '<div id="left">'
        '<div id="shotpane"><div class="ph">\u9009\u4e2d\u8282\u70b9\u540e<br>\u6b64\u5904\u663e\u793a\u8be5\u73af\u8282\u89c6\u53e3\u622a\u56fe</div><div id="shotcap"></div></div>'
        '<div id="hsplit"></div>'
        '<div id="side"></div>'
        '</div>'
        '<div id="vsplit"></div>'
        '<div id="wrap"><svg id="g"><g id="gr"></g></svg></div>'
        '</div>'
        '<div id="mini">' + _esc(meta.get("desc", "")) + '</div>'
        '<div id="ov"><img/></div>'
        '<script>var DATA=' + json.dumps(data, ensure_ascii=False) + ';</script>'
        '<script>' + JS + '</script></body></html>'
    )
