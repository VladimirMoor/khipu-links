// Knot determinant |Δ(-1)| of an open cord (ends far up and down the z axis, closed by a big arc): 1 for no knot,
// 3 overhand (trefoil), 5 figure-eight, 7 double overhand (5_2), 11 triple overhand (7_2) ...
window.knotDet=function(pts){
  const zs=pts.map(p=>p[2]), top=Math.min(...zs)-50, bot=Math.max(...zs)+50;
  const P=[[0,0,top],...pts,[0,0,bot],[500,0,bot],[500,0,top]];   // closed polygon (last joins first)
  // generic projection: rotate by fixed odd angles
  const a=0.7123,b=0.3311,c=1.1717, ca=Math.cos(a),sa=Math.sin(a),cb=Math.cos(b),sb=Math.sin(b),cc=Math.cos(c),sc=Math.sin(c);
  const Q=P.map(([x,y,z])=>{ let X=x*ca-y*sa, Y=x*sa+y*ca, Z=z; let Y2=Y*cb-Z*sb, Z2=Y*sb+Z*cb; Y=Y2; Z=Z2; let X2=X*cc-Z*sc, Z3=X*sc+Z*cc; return [X2,Y,Z3] });
  const n=Q.length, X=[];
  for(let i=0;i<n;i++) for(let j=i+2;j<n;j++){ if(i===0&&j===n-1) continue;
    const p=Q[i],p2=Q[(i+1)%n],q=Q[j],q2=Q[(j+1)%n];
    const d1x=p2[0]-p[0],d1y=p2[1]-p[1],d2x=q2[0]-q[0],d2y=q2[1]-q[1], den=d1x*d2y-d1y*d2x; if(Math.abs(den)<1e-12) continue;
    const t=((q[0]-p[0])*d2y-(q[1]-p[1])*d2x)/den, u=((q[0]-p[0])*d1y-(q[1]-p[1])*d1x)/den;
    if(t<0||t>=1||u<0||u>=1) continue;
    const zi=p[2]+t*(p2[2]-p[2]), zj=q[2]+u*(q2[2]-q[2]);
    X.push({i,t,j,u,iOver:zi>zj}) }
  if(!X.length) return 1;
  // undercrossing positions along the curve split it into arcs
  const unders=X.map((x,k)=>({k,pos:x.iOver?x.j+x.u:x.i+x.t})).sort((A,B)=>A.pos-B.pos);
  const m=unders.length, arcOf=pos=>{ // arc index containing position pos (arc k starts at unders[k])
    let lo=-1; for(let k=0;k<m;k++) if(unders[k].pos<=pos) lo=k; return lo<0?m-1:lo };
  const rows=X.map((x,k)=>{ const overPos=x.iOver?x.i+x.t:x.j+x.u, underPos=x.iOver?x.j+x.u:x.i+x.t;
    const idx=unders.findIndex(U=>U.k===k), uIn=(idx-1+m)%m, uOut=idx, o=arcOf(overPos);
    const r=new Array(m).fill(0n); r[o]+=2n; r[uIn]-=1n; r[uOut]-=1n; return r });
  // determinant of the (m-1)x(m-1) minor, Bareiss
  const A=rows.slice(0,m-1).map(r=>r.slice(0,m-1)), N=m-1; if(N===0) return 1;
  let prev=1n, sign=1n;
  for(let k=0;k<N-1;k++){ if(A[k][k]===0n){ let s=k+1; while(s<N&&A[s][k]===0n) s++; if(s===N) return 0; [A[k],A[s]]=[A[s],A[k]]; sign=-sign }
    for(let i=k+1;i<N;i++) for(let j=k+1;j<N;j++) A[i][j]=(A[i][j]*A[k][k]-A[i][k]*A[k][j])/prev;
    prev=A[k][k] }
  let d=sign*A[N-1][N-1]; if(d<0n) d=-d; return Number(d) };
