"""Synthetic Verse digest fixtures - REAL digests are Epic-copyrighted
and per-install; these mimic the declaration shapes only."""

DIGEST_V41 = """\
# synthetic digest fixture (not Epic content)
Fortnite<public> := module:
    Devices<public> := module:
        creative_device<public> := class<abstract>():
            OnBegin<public>()<suspends>:void = external {}
            GetTransform<public>()<transacts>:transform = external {}
        button_device<public> := class<concrete>(creative_device):
            InteractedWithEvent<public>:listenable(agent) = external {}
            Enable<public>()<transacts>:void = external {}
            Disable<public>()<transacts>:void = external {}
            SetInteractionText<public>(Text:message)<transacts>:void = external {}
        fort_vehicle<public> := class<abstract>():
            GetPassengers<public>()<transacts>:[]agent = external {}
            Eject<public>(A:agent)<transacts>:void = external {}
Verse<public> := module:
    SceneGraph<public> := module:
        entity<public> := class<concrete>():
            AddComponents<public>(C:[]component)<transacts>:void = external {}
            GetComponent<public>()<decides><transacts>:component = external {}
        component<public> := class<abstract>():
            OnBegin<public>()<suspends>:void = external {}
"""

DIGEST_V42 = """\
# synthetic digest fixture (not Epic content)
Fortnite<public> := module:
    Devices<public> := module:
        creative_device<public> := class<abstract>():
            OnBegin<public>()<suspends>:void = external {}
            GetTransform<public>()<transacts>:transform = external {}
        button_device<public> := class<concrete>(creative_device):
            InteractedWithEvent<public>:listenable(agent) = external {}
            Enable<public>()<transacts>:void = external {}
            Disable<public>()<transacts>:void = external {}
            SetInteractionText<public>(Text:message)<transacts>:void = external {}
            HoldToInteractEvent<public>:listenable(agent) = external {}
        fort_vehicle<public> := class<abstract>():
            GetOccupants<public>()<transacts>:[]agent = external {}
            Eject<public>(A:agent)<reads><writes>:void = external {}
Verse<public> := module:
    SceneGraph<public> := module:
        entity<public> := class<concrete>():
            AddComponents<public>(C:[]component)<transacts>:void = external {}
            GetComponent<public>()<decides><transacts>:component = external {}
        component<public> := class<abstract>():
            OnBegin<public>()<suspends>:void = external {}
"""

CLEAN_SNIPPET = """
using { /Fortnite.com/Devices }
my_device := class(creative_device):
    @editable Button : button_device = button_device{}
    OnBegin<override>()<suspends> : void =
        Button.InteractedWithEvent.Subscribe(OnPressed)
        Button.Enable()
    OnPressed(Agent : agent) : void =
        Print("ok")
"""

HALLUCINATED_SNIPPET = """
using { /Fortnite.com/Devices }
bad_device := class(creative_device):
    @editable Button : button_device = button_device{}
    @editable Car : fort_vehicle = fort_vehicle{}
    DoThings<varies>() : void =
        Button.Explode()
        Car.GetPassengers()
        Button.MagicEvent.Subscribe(OnPressed)
    OnPressed(Agent : agent) : void =
        Print("ok")
"""
