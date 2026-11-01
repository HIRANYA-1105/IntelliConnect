"""
Small labeled dataset used to train the intent classifier at startup.

This stands in for a real historical-conversation dataset. For a production
system, replace this with actual labeled support transcripts (the more
examples per intent, the better the classifier generalizes) -- the training
code in ml/intent.py does not need to change, only this list.
"""

INTENT_EXAMPLES = [
    # ---- billing ----
    ("why is my bill so high this month", "billing"),
    ("I was overcharged on my last invoice", "billing"),
    ("please explain this extra charge on my bill", "billing"),
    ("I need a refund for a wrong deduction", "billing"),
    ("my payment failed but amount was deducted", "billing"),
    ("there is a roaming charge I don't recognize", "billing"),
    ("billing amount doesn't match my plan", "billing"),
    ("nenu extra amount pay chesanu enduku", "billing"),
    ("bill lo late fee vachindi enduku", "billing"),
    ("why did you charge me twice this month", "billing"),
    ("invoice lo oka charge ardam kaledu", "billing"),
    ("can you send me last month's invoice", "billing"),
    ("I want to dispute a charge on my account", "billing"),
    ("data addon charge padindi naku waste", "billing"),
    ("my recharge amount was not credited", "billing"),
    ("my recharge is not working", "billing"),
    ("recharge failed but amount deducted", "billing"),
    ("recharge is not working after payment", "billing"),
    ("my recharge didn't go through", "billing"),
    ("recharge not working even after payment", "billing"),
    ("paid for recharge but plan not activated", "billing"),
    ("recharge unsuccessful but money deducted", "billing"),

    # ---- network ----
    ("my internet has been down since morning", "network"),
    ("no network signal in my area", "network"),
    ("network is very slow today", "network"),
    ("call keeps dropping every few minutes", "network"),
    ("wifi is disconnecting again and again", "network"),
    ("signal ledu naa area lo", "network"),
    ("internet chala slow ga undi", "network"),
    ("network down aipoyindi rendu gantala nunchi", "network"),
    ("broadband connection is not working", "network"),
    ("4g speed is extremely poor near my house", "network"),
    ("outage in my locality since last night", "network"),
    ("mobile data not working outdoors", "network"),
    ("network is not stable during calls", "network"),
    ("service interruption in our building", "network"),
    ("router lights are showing red, no internet", "network"),

    # ---- plan_change ----
    ("I want to upgrade my current plan", "plan_change"),
    ("please switch me to the unlimited plan", "plan_change"),
    ("what plans do you have with more data", "plan_change"),
    ("I want to downgrade to a cheaper plan", "plan_change"),
    ("recharge cheyali naaku better plan kavali", "plan_change"),
    ("plan change cheyali data ekkuva kavali", "plan_change"),
    ("suggest me a good family plan", "plan_change"),
    ("can I switch to postpaid from prepaid", "plan_change"),
    ("what is the validity of the unlimited pack", "plan_change"),
    ("I need more data every month", "plan_change"),
    ("change my subscription to yearly plan", "plan_change"),
    ("is there a student discount plan available", "plan_change"),
    ("tell me my plan what I have to recharge", "plan_change"),
    ("what recharge should I do", "plan_change"),
    ("analyse my past usage and tell me what I need", "plan_change"),
    ("based on my usage what plan is best for me", "plan_change"),
    ("compare plans for me based on my usage", "plan_change"),
    ("which recharge plan suits me", "plan_change"),
    ("suggest a recharge based on my usage", "plan_change"),
    ("what should I recharge with this month", "plan_change"),
    ("recommend a plan based on how much data I use", "plan_change"),
    ("naa usage batti evi recharge cheyali", "plan_change"),
    ("which plan is best for my usage", "plan_change"),

    # ---- sim ----
    ("my new sim is not activating", "sim"),
    ("I want to port my number to your network", "sim"),
    ("sim card is not detected in my phone", "sim"),
    ("how do I activate esim on my device", "sim"),
    ("sim activate avvatledu", "sim"),
    ("number port cheyali different network nunchi", "sim"),
    ("lost my sim card need a replacement", "sim"),
    ("device is not recognizing the sim", "sim"),
    ("esim QR code work avvatledu", "sim"),
    ("I need a new sim for my second phone", "sim"),

    # ---- cancel ----
    ("I want to cancel my subscription", "cancel"),
    ("please close my account permanently", "cancel"),
    ("how do I terminate my connection", "cancel"),
    ("account cancel cheyali naaku", "cancel"),
    ("connection close chesi ivvu", "cancel"),
    ("I am switching to another operator, cancel this", "cancel"),
    ("this service is useless, cancel my plan", "cancel"),
    ("I want to stop auto-renewal and close the account", "cancel"),
    ("terminate my broadband connection please", "cancel"),

    # ---- general ----
    ("hi I need some help", "general"),
    ("what are your customer care hours", "general"),
    ("how can I contact a human agent", "general"),
    ("thank you for your help", "general"),
    ("naaku oka doubt undi", "general"),
    ("customer care number cheppu", "general"),
    ("is this chat available 24/7", "general"),
    ("hello, good morning", "general"),
    ("can you help me with something else", "general"),
    ("what services do you offer", "general"),
]
