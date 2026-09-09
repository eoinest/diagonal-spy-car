"""Photo-informed 251 epoxy contour within the published 4 A package envelope.
The manufacturer dimensions the envelope, not this coating profile.
"""
import math
import bpy, bmesh

def epoxy_body(register):
    # Axial coordinate and radius in mm. Rounded shoulders and shallow waist
    # follow the family reference photograph; these are not measured tolerances.
    half=[(0,1.24),(.7,1.27),(1.5,1.39),(1.8,1.40),(2.2,1.35),
          (2.6,1.20),(3.0,.95),(3.3,.60),(3.555,.32)]
    profile=[(-y,r) for y,r in reversed(half[1:])]+half
    # Shared monotone cubic slopes avoid artificial rings at the profile keys.
    h=[b[0]-a[0] for a,b in zip(profile,profile[1:])]
    d=[(b[1]-a[1])/step for a,b,step in zip(profile,profile[1:],h)]
    slopes=[d[0]]
    for i in range(1,len(profile)-1):
        if d[i-1]*d[i]<=0:slopes.append(0.0)
        else:
            w1=2*h[i]+h[i-1];w2=h[i]+2*h[i-1]
            slopes.append((w1+w2)/(w1/d[i-1]+w2/d[i]))
    slopes.append(d[-1])
    rings=[]
    for i,((y0,r0),(y1,r1)) in enumerate(zip(profile,profile[1:])):
        for k in range(12):
            t=k/12
            r=(2*t**3-3*t**2+1)*r0+(t**3-2*t**2+t)*h[i]*slopes[i]
            r+=(-2*t**3+3*t**2)*r1+(t**3-t**2)*h[i]*slopes[i+1]
            rings.append((y0+(y1-y0)*t,r))
    rings.append(profile[-1])
    sides=96
    verts=[(r*math.cos(2*math.pi*j/sides),y,r*math.sin(2*math.pi*j/sides))
           for y,r in rings for j in range(sides)]
    faces=[]
    for i in range(len(rings)-1):
        for j in range(sides):
            a=i*sides+j;b=i*sides+(j+1)%sides
            faces.append((a,a+sides,b+sides,b))
    # Caps disappear into the tin lead at the tapered coating exits.
    faces.append(tuple(range(sides)))
    faces.append(tuple((len(rings)-1)*sides+j for j in reversed(range(sides))))
    mesh=bpy.data.meshes.new('251 rounded epoxy profile');mesh.from_pydata(verts,[],faces);mesh.update()
    bm=bmesh.new();bm.from_mesh(mesh)
    assert all(e.is_manifold for e in bm.edges), 'Fuse shell is not manifold'
    assert bm.calc_volume(signed=True)>0, 'Fuse shell orientation is invalid'
    bm.free()
    o=register(bpy.data.objects.new('251 epoxy',mesh),'F_IN 0251004.MXL body','green')
    o.location=(-15,0,20.2)
    for p in mesh.polygons:p.use_smooth=len(p.vertices)==4
    o['dimension_status']='7.11 mm long x 2.80 mm maximum diameter; rounded coating contour is photo-informed, not manufacturer CAD'
    o['appearance_source']='electronics/guide-assets/fuse-pico-251.jpg; representative 251 family photograph'
    return o

def formed_lead_points(sign):
    pts=[(-15,sign*3.50,20.2),(-15,sign*5.5,20.2)]
    # Two 1 mm centerline-radius bends, outside the holder end stops.
    for k in range(1,25):
        t=k*math.pi/48;pts.append((-15,sign*(5.5+math.sin(t)),19.2+math.cos(t)))
    pts.append((-15,sign*6.5,18.0))
    for k in range(1,25):
        t=k*math.pi/48;pts.append((-15,sign*(7.5-math.cos(t)),18.0-math.sin(t)))
    pts.append((-15,sign*8.5,17.0))
    return pts
