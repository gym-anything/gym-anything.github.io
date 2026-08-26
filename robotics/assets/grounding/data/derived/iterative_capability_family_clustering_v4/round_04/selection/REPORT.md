# k1–k5 three-mode action-group selection

This is the frozen 100-slot pipeline run under three coverage definitions. The candidate pool, policy targets, budgets, sequence, and tie breaks are shared; only the active capability domains differ.

## Headline coverage

| Mode | Economy | Strategic min | STEM min | SOC min | Covered actions | Family min |
|---|---:|---:|---:|---:|---:|---:|
| physics_only | 83.22475265516979639095209496020202080892554213127046247196047487031051019752248940017039520667227102% | 82.15416105067254681837144288228573272947755412765762561550535713403837941436597343338026560567588565% | 86.84911788046831813482881180217665784719271794756632671350689896016156208467947953394127192047737675% | 81.42638364768759021378623892454111078748581130912690263448018847993352527026260214719880878616193156% | 6,754 | 74.53490698139627925585117023404680936187237447489497899579915983196639327865573114622924584916983415% |
| physics_plus_robotics | 66.33412115246462196970588152747427463758287197357698551115040864088194305746168467316319727270685897% | 63.55428669989352904686934839700916527550095604977558095417025428896182267631185869033438249912822135% | 77.22364333181858167993002399546922471897528253653862766904955136407569552122382050769410541000891771% | 62.53389434605696773582746963081106950093861539231753080126317306526665628027298648017790593641848728% | 4,614 | 63.63885330556688876937756858489122956871825975454591962306593368275547517245644715921223997273580854% |
| robotics_only | 86.72510477209179124298041710894543315720692881049443971009241516494544562602692890151557005583119838% | 85.866230604122150458690673360987745908669355402618742552481770150953090760778379407161968049770018% | 92.6408759924358249665668187835537284865836639193688986231137118021974765885538128956357626717578376% | 83.61654485725987338150832296760168353063667247482446962319570137288908397067372009861912288605075202% | 7,224 | 71.65997342244630747884543979988665455042895389966973481073264153524457212092786930097125324891051595% |

## Cross-mode overlap

All three portfolios share **1** action groups.

| Pair | Shared actions | Jaccard |
|---|---:|---:|
| physics_only × physics_plus_robotics | 27 | 0.1561 |
| physics_only × robotics_only | 8 | 0.0417 |
| physics_plus_robotics × robotics_only | 16 | 0.0870 |

## physics_only


### k1_economic_core

- operate vehicle controls to drive the vehicle along a test route (`375`)
- push gate latch to test lock status (`586`)
- position polishing machine on target surface (`2381`)
- Scan underground transmission cable for physical damage (`3172`)
- manipulate control lever to position piling leads (`3554`)
- Fasten replacement lock assembly onto door (`3594`)
- restrain target animal using capture net or noose (`4067`)
- position an appliance component on a workstation (`4350`)
- Move signal batons to display marshalling signals (`4533`)
- write tax values in entry boxes on tax form (`4658`)
- press seed into soil with a roller tool (`4854`)
- dispense pest control treatments onto targeted areas (`5204`)
- thread pipe end (`5551`)
- bevel edge of stone surface using grinding tool (`5663`)
- Insert plant seedling into planter mechanism slot (`6064`)
- rotate sweep board (`6465`)
- Carry supply item to target area (`8366`)
- unfold plastic film across repair area (`8377`)
- actuate control switch on testing apparatus (`8652`)
- apply glue to joining surfaces of wood parts (`8867`)

### k2_1_strategic_domains

- retract measuring tool from vessel hold (`397`)
- track patient eye movements using a camera (`1206`)
- draw fluid specimen into the specimen tube (`1940`)
- escort children across road surface (`3315`)
- unzip a bag (`3319`)
- add disease treatment agent to hatchery water (`3391`)
- Rotate key inside door lock cylinder (`3783`)
- escort offender on foot to target location (`4262`)
- Suture oral tissue using a needle holder (`4374`)
- observe wash cycle status on washer display (`4396`)
- wipe the newborn infant with a towel (`5338`)
- engage brakes on transport equipment (`5409`)
- depress syringe plunger to inject liquid dose (`5712`)
- Latch the quarantine enclosure gate (`6194`)
- connect oxygen tubing coupler onto valve nozzle of replacement cylinder (`6691`)
- Wipe child's skin using soap and wet washcloth (`7225`)
- scrub station floor with soapy water (`8104`)
- flatten tissue specimen on glass slide surface (`8297`)
- position a patient in a postural drainage posture (`9225`)
- move a food utensil to a patient mouth (`9292`)

### k2_2_stem_research

- monitor prototype model or aerospace equipment using measurement instruments or cameras (`5`)
- transfer solid, liquid, or gaseous sample into test vessel (`1575`)
- inspect control panel displays and alarm indicators (`2103`)
- rinse decontamination residues from the equipment surface (`3384`)
- Adjust focus controls on analysis instrument (`4351`)
- measure the load response using a sensor (`4448`)
- scan sample with microscope camera to record cellular features (`4800`)
- dispense reagent solution into test vessel (`5433`)
- Mix catalyst materials in a container (`5883`)
- clip a vegetation sample from the ground plot (`6426`)
- plug power cable into wall outlet or device jack (`6477`)
- Attach diagnostic equipment cable to hardware test interface (`6626`)
- draw air sample into aerosol detection system (`6835`)
- coat object surface with fluorescent dye penetrant (`6860`)
- transfer liquid reagent into test tube (`7952`)
- collect a water sample from a geographic water source (`8037`)
- cut organ or tissue sample into thin sections (`8038`)
- remove prototype model or aerospace equipment from test fixture or environmental chamber (`8459`)
- Mount aerial photo plates onto stereoplotting apparatus (`8902`)
- acquire voltage reading from electrical test point (`9275`)

### k3_soc_major_diversity

- remove debris from irrigation ditch using shovel (`6443`) — 45
- pick mature crop from plant stem (`6994`) — 45
- tamp soil around base of post in hole (`7327`) — 45
- Actuate control switches on power plant equipment (`7786`) — 51
- Extract plant from soil with root ball (`3890`) — 45
- remove trash bag from waste bin (`7906`) — 37
- steer an all-terrain vehicle across grazing land terrain (`8229`) — 45
- cut the meat section into custom customer portions (`8307`) — 51
- open vehicle compartment hatch (`7492`) — 21
- apply weld joints along track interfaces using welding equipment (`13`) — 49
- aim a barcode scanner at a product item tag (`3438`) — 11
- pass vacuum cleaner nozzle across rug or carpet (`8502`) — 37
- rake fallen leaves and debris (`3274`) — 45
- pass trowel or float over leveled surface (`3821`) — 47
- adjust laboratory equipment mechanical fittings (`9235`) — 49
- guide lawn mower across grass (`4420`) — 45
- rotate a fire hose valve to open position (`8918`) — 51
- fill the coffee brewer basket with ground coffee (`5569`) — 51
- tighten lug nuts on wheel studs (`7371`) — 49
- Drive bit into concrete or pavement until surface fractures (`5908`) — 47
- guide powered waxing or polishing machine across floor surface (`7996`) — 37
- Hitch implement to tractor (`7433`) — 45
- trim nonhh adult's hair with clippers (`8974`) — 39

### k4_niche_occupations

- perform stage movements (`6047`) — Music Therapists
- wave a baton to direct tempo for a choir (`7963`) — Music Directors and Composers
- Collect insect specimens from host plants or soil using a collection vial (`5838`) — Conservation Scientists
- measure site boundary dimension (`3535`) — Urban and Regional Planners
- observe the conductor with a visual sensor to detect starting signals (`349`) — Locomotive Engineers
- scan track ahead (`1090`) — Locomotive Engineers
- read cab instrument gauges (`2802`) — Locomotive Engineers
- adjust seat height on a fitness machine (`5098`) — Fitness and Wellness Coordinators
- raise a sheared tree using a hydraulic boom (`3254`) — Logging Equipment Operators

### k5_capability_family_fill

- Reel in fishing line (`5957`) — aerodynamics
- track thermal state of workpieces during processing (`1810`) — thermal_phase_change
- Dry tooth surfaces using an air syringe (`3607`) — aerodynamics
- steer tractor with contouring implement along slope (`1998`) — granular_matter
- direct hot-air welding gun stream onto plastic panel (`3867`) — thermal_phase_change
- Observe recovering animal condition (`1083`) — other_physics
- acquire measurement coordinates of field location (`337`) — aerodynamics
- Measure rate of timepiece on watch-rate recorder (`2493`) — other_physics

## physics_plus_robotics


### k1_economic_core

- tactilely measure clay wall thickness (`1047`)
- Fasten bone plate onto aligned facial bone segments with screws (`2497`)
- trace client signature on document surface using pen (`3326`)
- Put clothing onto body (`3501`)
- Drive a truck or cart carrying equipment, poultry, or livestock to destination (`3802`)
- Position rigging components such as cables, pulleys, or hooks (`4178`)
- transport a material item (`4269`)
- clear snow from switch boxes (`4288`)
- place evidence marker next to object (`4828`)
- spread erosion control matting onto degraded soil (`5524`)
- apply paint, dye, polish, reconditioner, or wax onto vehicle surfaces (`5647`)
- position patient's head against an ophthalmic headrest (`5742`)
- Insert plant seedling into planter mechanism slot (`6064`)
- collect test materials from the table surface (`6332`)
- attach test probes to supporting electrical or mechanical system terminals (`6608`)
- Engage vehicle throttle (`6738`)
- place luggage onto baggage cart (`7248`)
- Carry supply item to target area (`8366`)
- drill hole into marble or ornamental stone (`8924`)
- spread stucco onto exterior surface using a trowel (`8983`)

### k2_1_strategic_domains

- withdraw the calibrated rod from the vessel (`172`)
- Reinsert dipstick into engine block (`431`)
- track the operating equipment with a visual sensor (`2463`)
- observe fit and alignment of device on patient (`2706`)
- unzip a bag (`3319`)
- pull hand brake release lever to release brake (`4028`)
- escort (`4109`)
- observe wash cycle status on washer display (`4396`)
- position locomotive to align couplers with railcar (`4803`)
- align forklift forks with load (`5007`)
- change bed linens on patient bed (`5075`)
- wrap inflatable blood pressure cuff around upper arm (`5106`)
- Position subject finger on scanner plate (`5141`)
- wipe the newborn infant with a towel (`5338`)
- position computer tower on desk (`5754`)
- Latch the quarantine enclosure gate (`6194`)
- connect oxygen tubing coupler onto valve nozzle of replacement cylinder (`6691`)
- scrub station floor with soapy water (`8104`)
- Position patient into required surgical posture (`8738`)
- Fasten securing straps of portable MRI scanner (`8785`)

### k2_2_stem_research

- observe status indicator lights (`425`)
- read measurement result on instrument display (`1264`)
- rinse decontamination residues from the equipment surface (`3384`)
- align a drafting instrument on drawing paper (`3662`)
- Pour chemical liquid into target container (`4315`)
- Adjust focus controls on analysis instrument (`4351`)
- measure the load response using a sensor (`4448`)
- collect process liquid samples from pilot plant sampling valve (`4509`)
- position prototype model or aerospace equipment into test fixture or environmental chamber (`4651`)
- Position a fermentation reactor vessel on a lab work surface (`5794`)
- Mix catalyst materials in a container (`5883`)
- calibrate validation test equipment (`5979`)
- Attach diagnostic equipment cable to hardware test interface (`6626`)
- draw air sample into aerosol detection system (`6835`)
- turn a calibration dial on laboratory equipment (`6935`)
- place toxic material container inside biosafety cabinet (`7254`)
- transfer liquid reagent into test tube (`7952`)
- collect a water sample from a geographic water source (`8037`)
- remove prototype model or aerospace equipment from test fixture or environmental chamber (`8459`)
- replace worn filter cartridge in equipment (`8945`)

### k3_soc_major_diversity

- Apply disinfectant solution to stalls, pens, or equipment (`5451`) — 45
- Extract plant from soil with root ball (`3890`) — 45
- remove trash bag from waste bin (`7906`) — 37
- board a vehicle (`7779`) — 45
- insert seeds or seedlings into soil (`7548`) — 45
- hand a flyer to a person (`7981`) — 21
- vacuum cleanroom surfaces or floors (`4638`) — 37
- dig earth with pick or shovel (`4204`) — 47
- steer a tractor along a route (`4986`) — 45
- extend arms outward for a security checkpoint search (`3652`) — 11
- level ground surface (`6993`) — 47
- pick mature crop from plant stem (`6994`) — 45
- measure output reading from exercise or testing equipment (`119`) — 49
- open an entrance door for arriving visitors (`7131`) — 21
- guide powered waxing or polishing machine across floor surface (`7996`) — 37
- drill blast holes into rock formation or rocky area (`8840`) — 47
- guide power cleaning machine across floor surface (`6112`) — 37
- trim animal coat (`3587`) — 39
- fasten replacement roofing shingles or panels (`5330`) — 47
- adjust laboratory equipment mechanical fittings (`9235`) — 49
- guide a student with a disability to a facility such as a restroom (`7800`) — 21
- guide lawn mower across grass (`4420`) — 45
- Rotate key inside door lock cylinder (`3783`) — 33

### k4_niche_occupations

- maintain an extended posture for security inspection (`4437`) — Models
- perform stage movements (`6047`) — Music Therapists
- observe the conductor with a visual sensor to detect starting signals (`349`) — Locomotive Engineers
- raise one leg into extended posture (`703`) — Choreographers
- skin viscera (`4699`) — Slaughterers and Meat Packers
- wave a baton to direct tempo for a choir (`7963`) — Music Directors and Composers
- touch a drip torch flame to designated fuel and brush piles (`7762`) — Foresters
- scan forest terrain and sky with sensors (`2799`) — Forest Fire Inspectors and Prevention Specialists
- press smoothing tool along article seams (`4281`) — Sewers, Hand

### k5_capability_family_fill

- position a patient on a stress testing treadmill (`638`) — bimanual_coordination
- weld part components together using a welding torch or electrode (`4752`) — thermal_phase_change
- manipulate flight control yoke or stick to fly aircraft to specified test altitude (`2825`) — aerodynamics
- grade backfill soil along slopes using a blade (`5320`) — granular_matter
- Track handling of radioactive materials (`661`) — other_robot
- measure wind speed using a sensing instrument (`391`) — aerodynamics
- Position the tip of a torch or soldering tool at the defective joint or leak location (`8584`) — other_robot
- decant top liquid layer from extraction vessel (`5715`) — other_robot

## robotics_only


### k1_economic_core

- apply resistive force to client limb (`1567`)
- locate materials or textbooks on a storage shelf (`2184`)
- monitor temperature and pressure readings on the apparatus gauge (`2700`)
- advance drill bit into substrate to bore well hole (`4164`)
- position crane hook over subassembly (`4275`)
- guide a spinning cutoff wheel along the cut line of cured materials (`4704`)
- place evidence marker next to object (`4828`)
- scrub the target skin area of the patient (`5165`)
- hand out rhythm instruments to children (`5172`)
- grasp loose wires from the work area (`5588`)
- pass vacuum nozzle across floor surface (`5888`)
- align replacement part in device (`6494`)
- drive a bulldozer blade against weeds, brush, and logging debris on the site (`6531`)
- Manipulate locomotive controls to drive to roundhouse station (`6976`)
- transport meat carcass to butcher shop (`7243`)
- hand a bet receipt to a player (`7626`)
- measure dimensions of target wall or ceiling surface (`7887`)
- connect electrical cables between renewable energy source and system terminals (`8415`)
- spray water onto deck surface (`8663`)
- transfer unclaimed personal effects into a disposition bin (`8673`)

### k2_1_strategic_domains

- deflate catheter retention balloon (`745`)
- reach end-effector toward merchandise (`2161`)
- escort children across road surface (`3315`)
- aim a barcode scanner at a product item tag (`3438`)
- scan a handheld inspection probe past a target object (`3582`)
- wrap tie-down strap around load (`3688`)
- traverse assigned forest terrain (`3961`)
- Position protective equipment onto designated body region of athlete (`4205`)
- insert syringe needle into oral tissue (`4624`)
- align forklift forks with load (`5007`)
- pour fresh oil into a machine oil filler neck (`5045`)
- steer a moving vehicle to an appliance repair location (`5637`)
- lay clean sheet onto mattress (`5673`)
- position computer tower on desk (`5754`)
- deal playing cards to patients (`6418`)
- restrain a security threat (`6466`)
- Escort a student to a restroom facility (`7061`)
- Hold target stretch posture for specified duration (`7424`)
- put clean clothing onto patient body (`7489`)
- support student during ambulation toward facility (`9102`)

### k2_2_stem_research

- monitor sensor output during operation (`1142`)
- transfer compound sample into sample container (`2486`)
- dispense measured reagent into container (`2634`)
- Align a camera toward plant switchboard gauges and indicators (`3279`)
- position shelter structure in animal habitat area (`3345`)
- detach test probe from electromechanical test point (`3450`)
- align a drafting instrument on drawing paper (`3662`)
- disconnect test cables from photonics component (`3689`)
- mix the contents of the reaction vessel (`3754`)
- detach rock specimen from geological formation (`3952`)
- collect process liquid samples from pilot plant sampling valve (`4509`)
- Hold a child's bicycle to stabilize it (`4555`)
- position prototype model or aerospace equipment into test fixture or environmental chamber (`4651`)
- scan sample with microscope camera to record cellular features (`4800`)
- Direct abrasive blast stream from sandblasting nozzle onto contaminated object surface (`4893`)
- calibrate validation test equipment (`5979`)
- Lift fire extinguisher from mounting bracket (`6657`)
- tighten lug nuts on wheel studs (`7371`)
- Insert fiber optic cable into connector body (`8761`)
- machine component blank into finished geometry (`8819`)

### k3_soc_major_diversity

- sever a tree base using a harvester saw attachment (`3625`) — 45
- open an entrance door for arriving visitors (`7131`) — 21
- board a vehicle (`7779`) — 45
- guide a student with a disability to a facility such as a restroom (`7800`) — 21
- raise a sheared tree using a hydraulic boom (`3254`) — 45
- rake fallen leaves and debris (`3274`) — 45
- guide lawn mower across grass (`4420`) — 45
- collate paper pages into reports (`4035`) — 21
- dig earth with pick or shovel (`4204`) — 47
- discharge suppressant onto fire (`7218`) — 45
- tighten bolt on mounting frame with a socket wrench (`4230`) — 47
- mount air sampling filter cassette onto monitoring tower bracket (`8339`) — 27
- extend arms outward for a security checkpoint search (`3652`) — 11
- compact earth using pneumatic tamper (`8815`) — 47
- orient optical sensor toward nonhh adult (`7100`) — 21
- guide power cleaning machine across floor surface (`6112`) — 37
- apply drywall compound to high ceiling surface (`5400`) — 47
- Hitch implement to tractor (`7433`) — 45
- connect replacement wiring or instrument components (`6406`) — 47
- dump material into a truck bed (`5247`) — 47
- rub surface with cloth to produce shine (`4192`) — 37
- align paper map on digitizing tablet (`7758`) — 27
- apply post-harvest liquid treatment to crops (`4060`) — 45

### k4_niche_occupations

- visually scan survey response form for marking errors (`2320`) — Statistical Assistants
- maintain an extended posture for security inspection (`4437`) — Models
- record observation data (`2657`) — Cost Estimators
- raise one leg into extended posture (`703`) — Choreographers
- navigate between gaming tables on the casino floor (`2895`) — Gambling Managers
- observe dancers performing experimental dance steps (`2837`) — Choreographers
- Feed paper sheet into laminating machine (`7930`) — Speech-Language Pathology Assistants
- observe engine temperature gauges during warmup period (`3158`) — Railroad Brake, Signal, and Switch Operators and Locomotive Firers
- Place timecards into distribution racks (`4276`) — Payroll and Timekeeping Clerks

### k5_capability_family_fill

- Move blowtorch flame over floor covering material until softened (`5867`) — other_robot
- Track laboratory activity with camera (`324`) — other_robot
- Apply powder and solvent mixture onto paper forms and nails (`5342`) — other_robot
- Manipulate craft materials to demonstrate handicraft techniques (`1088`) — other_robot
- detect beat timing from audio stream (`3121`) — other_robot
- vocalize paging message into microphone (`1780`) — other_robot
- lower measuring tool into vessel hold (`8355`) — other_robot
- count checks in cash drawer tray (`1201`) — other_robot

## Interpretation guardrails

- k1, k2.1, and k2.2 are unordered joint MILP batches. Their displayed order is only stable index order.
- k3, k4, and k5 are sequential; their recorded step and active SOC, occupation, or family explain each choice.
- Coverage uses only identical or directly confirmed same-domain capability equivalence at sufficient level; no transitive closure is used.
- A result says that the portfolio supplies the modeled requirements, not that an environment or robot implementation already exists.
