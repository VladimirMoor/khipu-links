// Knot shapes for the 3D khipu models (site/knots.json), and a copy of the site's rope drawing to look at them.
// Units: the cord radius (cord thickness 2). Local frame: x toward the viewer, z down the cord.
//
// Each knot is laid out the way it is tied, with the right topology (checked with the knot determinant, knotdet.js),
// then pulled tight by a small simulation: the line is smoothed toward its neighbours (tension) while no two parts of
// the cord may come closer than one cord thickness (slightly less: cotton gives) and the cord cannot bend tighter than
// about its own thickness; the steps are small, so the cord never passes through itself.
window.ROPE=(()=>{
const PARAM={D:1.9, k:0.45, rho:1.15, iters:1500, itersLong:300, PLY:0.55};

// ---- rope drawing (as on the site) ----
const texCache={}, matCache={};
function plyCanvas(a,b,bump){ const W2=64,H2=32, c=document.createElement('canvas'); c.width=W2; c.height=H2; const g=c.getContext('2d');
  const im=g.createImageData(W2,H2), ca=new T.Color(a), cb=new T.Color(b);
  for(let y=0;y<H2;y++) for(let x=0;x<W2;x++){
    const ph=((x/W2)+(y/H2))*2, f=ph-Math.floor(ph), ply=Math.floor(ph)%2;
    const groove=Math.pow(Math.sin(Math.PI*f),0.6);
    const fibre=0.85+0.15*Math.sin((x*7.3+y*13.1)+Math.sin(x*1.7)*3)*Math.sin(y*2.1+x*0.4);
    const sh=(0.45+0.55*groove)*fibre, o=(y*W2+x)*4;
    if(bump){ const v=Math.round(255*sh); im.data[o]=im.data[o+1]=im.data[o+2]=v }
    else { const c0=ply?cb:ca; im.data[o]=Math.min(255,c0.r*255*sh*1.08); im.data[o+1]=Math.min(255,c0.g*255*sh*1.08); im.data[o+2]=Math.min(255,c0.b*255*sh*1.08) }
    im.data[o+3]=255 }
  g.putImageData(im,0,0); const t=new T.CanvasTexture(c); t.wrapS=t.wrapT=T.RepeatWrapping; t.anisotropy=4; return t }
let bumpTex=null;
const ropeMat=(a,b)=>{ if(!bumpTex) bumpTex=plyCanvas('#fff','#fff',true); const k=a+'|'+b; if(matCache[k]) return matCache[k];
  if(!texCache[k]) texCache[k]=plyCanvas(a,b,false);
  return matCache[k]=new T.MeshStandardMaterial({map:texCache[k],bumpMap:bumpTex,bumpScale:0.035,roughness:.97,metalness:0}) };
function ropeLine(Pts,r,radial){ const n=Pts.length, pos=new Float32Array(n*(radial+1)*3), nor=new Float32Array(n*(radial+1)*3), uv=new Float32Array(n*(radial+1)*2), idx=[];
  const t=new T.Vector3(), prevT=new T.Vector3(), N=new T.Vector3(), B=new T.Vector3(), tmpv=new T.Vector3(), q=new T.Quaternion(); let len=0;
  for(let k=0;k<n;k++){ if(k<n-1) t.subVectors(Pts[k+1],Pts[k>0?k-1:k]); else t.subVectors(Pts[k],Pts[k-1]); t.normalize();
    if(k===0){ const ref=Math.abs(t.y)<0.9?new T.Vector3(0,1,0):new T.Vector3(1,0,0); N.crossVectors(t,ref).normalize() }
    else { q.setFromUnitVectors(prevT,t); N.applyQuaternion(q).normalize(); len+=Pts[k].distanceTo(Pts[k-1]) }
    B.crossVectors(t,N); prevT.copy(t);
    for(let j=0;j<=radial;j++){ const a=j/radial*Math.PI*2, c=Math.cos(a), s2=Math.sin(a), o=k*(radial+1)+j;
      tmpv.copy(N).multiplyScalar(c).addScaledVector(B,s2);
      nor[o*3]=tmpv.x; nor[o*3+1]=tmpv.y; nor[o*3+2]=tmpv.z;
      pos[o*3]=Pts[k].x+r*tmpv.x; pos[o*3+1]=Pts[k].y+r*tmpv.y; pos[o*3+2]=Pts[k].z+r*tmpv.z;
      uv[o*2]=len/PARAM.PLY; uv[o*2+1]=j/radial }
    if(k>0) for(let j=0;j<radial;j++){ const a0=(k-1)*(radial+1)+j, b0=k*(radial+1)+j; idx.push(a0,a0+1,b0, b0,a0+1,b0+1) } }   // counter-clockwise seen from outside
  const g=new T.BufferGeometry(); g.setAttribute('position',new T.BufferAttribute(pos,3)); g.setAttribute('normal',new T.BufferAttribute(nor,3));
  g.setAttribute('uv',new T.BufferAttribute(uv,2)); g.setIndex(idx); g.computeBoundingSphere(); return g }

// ---- loose knots, laid out the way they are tied ----
// Single knot (overhand, determinant 3): a loop stretched along the cord, the end once round the loop's left side,
// through the loop, then down the front and on.
function looseSingle(){ const P=[], n=1, a=2.3, rx=4.6, rz=3.2+n*1.25, yt=2.4;
  const E=th=>[rx*Math.cos(th),0,rz*Math.sin(th)];
  for(let z=-30-rz;z<-rz-2;z+=1) P.push([1.5,0,z]);
  P.push([1.2,0,-rz-1]);
  const N=80; for(let q=0;q<=N;q++){ const u=q/N, th=-Math.PI/2+0.35+u*(2*Math.PI-0.2), lift=yt*Math.max(0,Math.min(1,(u-0.6)/0.3)); const p=E(th); P.push([p[0],lift*lift/yt*(3-2*lift/yt),p[2]]) }
  const beta=Math.min(1.0,(n*2.15+0.6)/(2*rz)), th0=Math.PI-beta, th1=Math.PI+beta, S=E(th0);
  P.push([2.6,yt,-rz-0.4]); P.push([rx+1.2,yt+0.6,-rz*0.3]); P.push([rx*0.4,a+1.8,S[2]*0.8+1.5]); P.push([S[0]+0.4,a+1.2,S[2]+0.6]);
  const M=28*n; let last;
  for(let q=0;q<=M;q++){ const u=q/M, th=th0+(th1-th0)*u, C=E(th), ln=Math.hypot(C[0],C[2]), ni=[-C[0]/ln,0,-C[2]/ln], phi=Math.PI/2-u*n*2*Math.PI;
    last=[C[0]+a*Math.sin(phi)*ni[0], a*Math.cos(phi), C[2]+a*Math.sin(phi)*ni[2]]; P.push(last) }
  P.push([last[0]-0.3,a+2.4,last[2]+1.0]); P.push([last[0]*0.6,a+2.6,rz*0.5]); P.push([last[0]*0.3,a+1.5,rz+2.5]); P.push([0,0.6,rz+4.5]);
  for(let z=rz+6;z<=rz+30;z+=1) P.push([0,0,z]);
  return P }
// Figure-eight knot (4_1, determinant 5): the standard closed curve in the x-z plane (depth y), cut open at its topmost
// point; the top lead comes down into one side of the cut, the other side leaves over the top and down outside the knot.
function looseEight(){ const P=[];
  const f=t=>[2.2*(2+Math.cos(2*t))*Math.cos(3*t), 3.0*Math.sin(4*t), 2.2*(2+Math.cos(2*t))*Math.sin(3*t)];
  let ts=0, zm=1e9; for(let q=0;q<2000;q++){ const t=q/2000*2*Math.PI, z=f(t)[2]; if(z<zm){zm=z;ts=t} }
  const sg=Math.sign(f(ts+1e-3)[0]-f(ts-1e-3)[0])||1, g=t=>{ const p=f(t); return [sg*p[0],p[1],p[2]] };
  const d=0.32, A=[]; for(let q=0;q<=320;q++) A.push(g(ts+d+q/320*(2*Math.PI-2*d)));
  const xs=A.map(p=>p[0]), zs=A.map(p=>p[2]), minX=Math.min(...xs), maxZ=Math.max(...zs);
  const s0=A[0], e0=A[A.length-1];
  for(let z=-30;z<s0[2]-4;z+=1) P.push([s0[0]*Math.min(1,(z+30)/20),0,z]);
  P.push([s0[0]-0.6,s0[1]*0.5,s0[2]-1.6]); A.forEach(p=>P.push(p));
  P.push([e0[0]+0.9,e0[1],e0[2]-1.4]); P.push([e0[0]-0.5,e0[1]*0.5,e0[2]-3.2]); P.push([minX-1,0,zm-3.6]);
  P.push([minX-4,0,zm-1]); for(let z=zm+1;z<maxZ+3;z+=1.2) P.push([minX-4,0,z]);
  P.push([minX-2,0,maxZ+5]); P.push([0,0,maxZ+8]); for(let z=maxZ+10;z<=maxZ+34;z+=1) P.push([0,0,z]);
  return P }
// Long knot of n turns (the n-fold overhand, determinant 2n + 1), laid out tight and dressed as on the khipus: the cord
// comes down through the middle of the knot, turns out at the bottom and is wound n times round the axis going up; at
// the top it goes into the middle and down beside its own standing part, so the turns lie round two strands. A free
// simulation lets the turns of a long knot capsize into a tangle (there is no friction), so long knots get only a short
// tightening from this layout.
function looseLong(n){ const P=[], c=0.97, Rx=2.0, Ry=c+2.0, pitch=2.05, H=1.2+n*pitch;
  for(let z=-30;z<-2.5;z+=1) P.push([0,0,z]);
  P.push([0,-c*0.6,-1.2]);
  for(let z=0;z<=H+0.6;z+=0.8) P.push([0,-c,z]);
  const ph0=-Math.PI/2; P.push([0.9,-(c+0.9),H+1.0]);
  const tot=(n+0.5)*2*Math.PI, M=Math.round(28*(n+0.5)); let last;
  for(let q=0;q<=M;q++){ const u=q/M, ph=ph0+u*tot; last=[Rx*Math.cos(ph),Ry*Math.sin(ph),H-u*(H-0.9)]; P.push(last) }
  P.push([last[0]*0.5,last[1]*0.75,0.0]); P.push([0,c,0.9]);
  for(let z=1.7;z<=H+0.4;z+=0.8) P.push([0,c,z]);
  P.push([0,c*0.6,H+1.8]); P.push([0,0,H+3.2]);
  for(let z=H+4.2;z<=H+30;z+=1) P.push([0,0,z]);
  return P }

// ---- pulling tight ----
function resample(pts,h){ const cv=new T.CatmullRomCurve3(pts.map(v=>new T.Vector3(...v)),false,'centripetal'); const M=Math.round(cv.getLength()/h); return cv.getSpacedPoints(M).map(v=>[v.x,v.y,v.z]) }
function minGap(pts,h){ let m=1e9; const skip=Math.ceil(Math.PI*2/h); for(let i=0;i<pts.length;i++) for(let j=i+skip;j<pts.length;j++){ const d=Math.hypot(pts[i][0]-pts[j][0],pts[i][1]-pts[j][1],pts[i][2]-pts[j][2]); if(d<m) m=d } return m }
// stages: [[point spacing, iterations], ...] from coarse to fine. Both ends are pinned on the axis.
function tighten(raw,stages){ const D=PARAM.D, rho=PARAM.rho;
  let pts=resample(raw,stages[0][0]);
  for(const [hs,its] of stages){
    pts=resample(pts,hs); const top=pts[0][2], bot=pts[pts.length-1][2];
    // least distance between two points as a function of their distance along the cord: contact, and bending stiffness
    const REQ=[]; for(let k=0;k<4*D/hs+40;k++){ const s2=k*hs; REQ.push(Math.min(D,2*rho*Math.sin(Math.min(s2/(2*rho),Math.PI/2))*0.98)) }
    for(let it=0;it<its;it++){
      const n=pts.length, X=new Float64Array(n*3); for(let i=0;i<n;i++){ X[3*i]=pts[i][0]; X[3*i+1]=pts[i][1]; X[3*i+2]=pts[i][2] }
      const Y=X.slice(); for(let i=1;i<n-1;i++) for(let c=0;c<3;c++) Y[3*i+c]=X[3*i+c]+PARAM.k*((X[3*i-3+c]+X[3*i+3+c])/2-X[3*i+c]);
      Y[0]=0;Y[1]=0;Y[2]=top; Y[3*n-3]=0;Y[3*n-2]=0;Y[3*n-1]=bot;
      for(let pass=0;pass<3;pass++){ const grid=new Map(), key=(x,y,z)=>(x+512)*1048576+(y+512)*1024+(z+512);
        const C=new Int32Array(n*3); for(let i=0;i<n;i++){ C[3*i]=Math.floor(Y[3*i]/D); C[3*i+1]=Math.floor(Y[3*i+1]/D); C[3*i+2]=Math.floor(Y[3*i+2]/D); const k=key(C[3*i],C[3*i+1],C[3*i+2]); const L=grid.get(k); if(L) L.push(i); else grid.set(k,[i]) }
        for(let i=0;i<n;i++){ for(let dx=-1;dx<=1;dx++)for(let dy=-1;dy<=1;dy++)for(let dz=-1;dz<=1;dz++){ const L=grid.get(key(C[3*i]+dx,C[3*i+1]+dy,C[3*i+2]+dz)); if(!L) continue;
          for(const j of L){ if(j<=i+1) continue; const Dq=j-i<REQ.length?REQ[j-i]:D; const vx=Y[3*j]-Y[3*i], vy=Y[3*j+1]-Y[3*i+1], vz=Y[3*j+2]-Y[3*i+2], dd=Math.sqrt(vx*vx+vy*vy+vz*vz);
            if(dd<Dq&&dd>1e-9){ const m=(Dq-dd)/dd*0.5, wi=(i===0)?0:1, wj=(j===n-1)?0:1;
              Y[3*i]-=vx*m*wi; Y[3*i+1]-=vy*m*wi; Y[3*i+2]-=vz*m*wi; Y[3*j]+=vx*m*wj; Y[3*j+1]+=vy*m*wj; Y[3*j+2]+=vz*m*wj } } } } }
      for(let i=0;i<n;i++){ pts[i][0]=Y[3*i]; pts[i][1]=Y[3*i+1]; pts[i][2]=Y[3*i+2] }
      if(it%15===14){ pts=resample(pts,hs); pts[0]=[0,0,top]; pts[pts.length-1]=[0,0,bot] }
    }
  }
  return pts }

// ---- knot shapes: tightened, cut out, turned to face the viewer ----
const shapes={};
function knotShape(key){ if(shapes[key]) return shapes[key];
  const h=0.4, I=PARAM.iters, IL=PARAM.itersLong;
  const pts=key==='S'?tighten(looseSingle(),[[1.0,I*0.5],[0.6,I*0.3],[h,I*0.2]])
    :key==='E'?tighten(looseEight(),[[1.0,I*0.5],[0.6,I*0.3],[h,I*0.2]])
    :tighten(looseLong(+key.slice(1)),[[0.6,IL*0.5],[h,IL*0.5]]);
  // the knot is the part of the cord touching other parts of itself; keep a short run-in on each side
  const skip=Math.ceil(3*Math.PI/h), near=2.4, inK=new Array(pts.length).fill(false);
  for(let i=0;i<pts.length;i++) for(let j=i+skip;j<pts.length;j++){ const d=Math.hypot(pts[i][0]-pts[j][0],pts[i][1]-pts[j][1],pts[i][2]-pts[j][2]); if(d<near){ inK[i]=inK[j]=true } }
  let a=inK.indexOf(true), b=inK.lastIndexOf(true); a=Math.max(0,a-Math.round(2.5/h)); b=Math.min(pts.length-1,b+Math.round(2.5/h));
  // turn it so that entry and exit lie on the z axis; then round the axis so that the bulk of a single or figure-eight
  // knot faces +x (the viewer), and a long knot shows the broad side of its turns
  const seg=pts.slice(a,b+1).map(p=>new T.Vector3(...p)), o=seg[0].clone(), ax=seg[seg.length-1].clone().sub(o).normalize();
  const q=new T.Quaternion().setFromUnitVectors(ax,new T.Vector3(0,0,1)); seg.forEach(v=>v.sub(o).applyQuaternion(q));
  let mx=0,my=0; seg.forEach(v=>{mx+=v.x;my+=v.y});
  const rot=key[0]==='L'?Math.PI/2:-Math.atan2(my,mx), c=Math.cos(rot), s2=Math.sin(rot);
  return shapes[key]=seg.map(v=>[v.x*c-v.y*s2, v.x*s2+v.y*c, v.z]) }
const KEYS=['S','E','L2','L3','L4','L5','L6','L7','L8','L9'];
// the knots.json content: per shape a flat list x,y,z,... resampled every half radius, first point at the origin and
// last on the axis; with each shape's knot determinant and least gap for the record
function exportShapes(){ const out={}, report=[];
  for(const key of KEYS){ const seg=knotShape(key), cv=new T.CatmullRomCurve3(seg.map(p=>new T.Vector3(...p)));
    const pts=cv.getSpacedPoints(Math.round(cv.getLength()/0.5)).map(v=>[+v.x.toFixed(2),+v.y.toFixed(2),+v.z.toFixed(2)]);
    pts[0]=[0,0,0]; const e=pts[pts.length-1]; pts[pts.length-1]=[0,0,e[2]];
    out[key]=pts.flat(); report.push({key,points:pts.length,length:e[2],det:knotDet(pts),gap:+minGap(pts,0.5).toFixed(2)}) }
  return {out,report} }
return {PARAM,ropeMat,ropeLine,knotShape,exportShapes,KEYS};
})();
