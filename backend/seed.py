"""Seed the Vanguard Fitness database.

Populates 10 standard exercises and 10 PED/peptide reference profiles.
The script is idempotent: rows are matched on their unique ``slug`` and
updated in place, so re-running it never creates duplicates.

    python seed.py            # create tables (if needed) and seed
    python seed.py --reset    # drop and recreate every table first
"""

from __future__ import annotations

import argparse
import sys

from sqlalchemy import select

from app.database import Base, SessionLocal, engine, init_db
from app.models import Exercise, PEDProfile

# --------------------------------------------------------------------------- exercises
EXERCISES: list[dict] = [
    {
        "name": "Barbell Back Squat",
        "slug": "barbell-back-squat",
        "muscle_group": "Legs",
        "secondary_muscles": "Glutes, Hamstrings, Erector Spinae, Core",
        "equipment": "Barbell",
        "mechanic": "compound",
        "difficulty": "intermediate",
        "description": (
            "The foundational lower-body strength lift. The bar rests across the upper back "
            "while you squat to at least parallel and drive back up."
        ),
        "form_instructions": (
            "1. Set the rack hooks at mid-chest height and the safety pins just below your "
            "bottom position.\n"
            "2. Place the bar across your rear delts (low bar) or upper traps (high bar), grip "
            "just outside the shoulders, and pull your elbows down to lock the bar in place.\n"
            "3. Unrack by standing tall, then take two controlled steps back. Set your feet "
            "shoulder-width with toes turned out 15-30 degrees.\n"
            "4. Take a deep breath into your belly and brace your midsection as if bracing for "
            "a punch.\n"
            "5. Break at the hips and knees together, tracking your knees over your toes, and "
            "descend until your hip crease is at or below the top of your knee.\n"
            "6. Drive through the whole foot and push the floor away, keeping your chest and "
            "hips rising at the same rate.\n"
            "7. Exhale at the top and reset your brace before the next rep."
        ),
        "common_mistakes": (
            "Knees caving inward under load; heels lifting off the floor; the hips shooting up "
            "faster than the chest, turning the squat into a good morning; rounding the lower "
            "back at the bottom; bouncing out of the hole instead of controlling the descent."
        ),
        "safety_notes": (
            "Always squat inside a rack with the safety pins set. Never bail forward over the "
            "bar - if you miss a rep, sit back and let the pins catch the weight."
        ),
    },
    {
        "name": "Conventional Deadlift",
        "slug": "conventional-deadlift",
        "muscle_group": "Back",
        "secondary_muscles": "Glutes, Hamstrings, Traps, Forearms, Core",
        "equipment": "Barbell",
        "mechanic": "compound",
        "difficulty": "advanced",
        "description": (
            "A full-body hip hinge that lifts the bar from the floor to a standing lockout. The "
            "single heaviest expression of posterior-chain strength."
        ),
        "form_instructions": (
            "1. Stand with mid-foot under the bar, feet roughly hip-width apart.\n"
            "2. Hinge at the hips and grip the bar just outside your shins, double overhand or "
            "mixed grip.\n"
            "3. Drop your hips until your shins touch the bar, then lift your chest to pull the "
            "slack out of the bar - you should hear it click into the plates.\n"
            "4. Brace hard, set your lats by imagining you are squeezing oranges in your "
            "armpits, and keep a neutral spine from head to hips.\n"
            "5. Push the floor away with your legs; once the bar passes the knees, drive your "
            "hips forward to lock out.\n"
            "6. Finish standing tall with glutes squeezed - do not lean back or hyperextend.\n"
            "7. Return the bar by hinging first, then bending the knees once it clears them."
        ),
        "common_mistakes": (
            "Yanking the bar off the floor without pulling the slack out; rounding the lumbar "
            "spine; letting the bar drift away from the shins; hyperextending the lower back at "
            "lockout; squatting the weight up instead of hinging."
        ),
        "safety_notes": (
            "Stop the set the moment your lower back rounds. Deadlifts are highly fatiguing - "
            "do not train them to failure."
        ),
    },
    {
        "name": "Barbell Bench Press",
        "slug": "barbell-bench-press",
        "muscle_group": "Chest",
        "secondary_muscles": "Front Delts, Triceps",
        "equipment": "Barbell",
        "mechanic": "compound",
        "difficulty": "intermediate",
        "description": (
            "The primary horizontal pressing lift for chest, front delt and triceps strength."
        ),
        "form_instructions": (
            "1. Lie on the bench with your eyes directly under the bar.\n"
            "2. Plant both feet flat, pinch your shoulder blades together and down, and hold a "
            "slight natural arch in your lower back.\n"
            "3. Grip the bar roughly 1.5x shoulder width and squeeze it hard.\n"
            "4. Unrack to a position directly over your shoulders, then take a breath and brace.\n"
            "5. Lower the bar under control to your lower chest / sternum, keeping your elbows "
            "at roughly 45-75 degrees from your torso - not flared to 90.\n"
            "6. Touch the chest without bouncing, then press up and slightly back toward your "
            "face until the elbows lock.\n"
            "7. Keep your shoulder blades retracted for every rep of the set."
        ),
        "common_mistakes": (
            "Flaring the elbows straight out to the sides, which stresses the shoulder joint; "
            "bouncing the bar off the chest; lifting the hips off the bench; letting the "
            "shoulder blades come unglued; uneven lockout between arms."
        ),
        "safety_notes": (
            "Use a spotter or safety arms whenever you train near failure. Never use a thumbless "
            "'suicide' grip - the bar can roll onto your chest or throat."
        ),
    },
    {
        "name": "Standing Overhead Press",
        "slug": "standing-overhead-press",
        "muscle_group": "Shoulders",
        "secondary_muscles": "Triceps, Upper Chest, Core",
        "equipment": "Barbell",
        "mechanic": "compound",
        "difficulty": "intermediate",
        "description": (
            "A strict standing press from the front rack to overhead lockout, built on total "
            "shoulder and trunk stability."
        ),
        "form_instructions": (
            "1. Set the bar at upper-chest height in the rack and grip it just outside "
            "shoulder-width.\n"
            "2. Unrack into a front rack position with the bar resting on your front delts and "
            "elbows slightly in front of the bar.\n"
            "3. Step back, set your feet hip-width, squeeze your glutes and brace your core.\n"
            "4. Pull your chin back slightly so the bar has a clear path past your face.\n"
            "5. Press straight up, and as the bar clears your forehead push your head 'through' "
            "the window so the bar finishes stacked over your mid-foot.\n"
            "6. Lock the elbows with the biceps beside your ears.\n"
            "7. Lower under control back to the front rack and reset your brace."
        ),
        "common_mistakes": (
            "Leaning back excessively and turning it into a standing incline press; pressing the "
            "bar around the face instead of moving the head back; losing the core brace and "
            "arching the lumbar spine; stopping short of full lockout."
        ),
        "safety_notes": (
            "If you cannot reach overhead lockout without arching your lower back, work on "
            "thoracic and shoulder mobility before loading the movement heavily."
        ),
    },
    {
        "name": "Pull-Up",
        "slug": "pull-up",
        "muscle_group": "Back",
        "secondary_muscles": "Biceps, Rear Delts, Forearms, Core",
        "equipment": "Bodyweight",
        "mechanic": "compound",
        "difficulty": "intermediate",
        "description": (
            "A vertical pull from a dead hang to chin-over-bar. The benchmark measure of "
            "relative upper-body pulling strength."
        ),
        "form_instructions": (
            "1. Grip the bar with an overhand grip slightly wider than your shoulders.\n"
            "2. Start from a full dead hang with the shoulders active, not collapsed into the "
            "joint.\n"
            "3. Depress and retract the shoulder blades first - the pull starts at the scapula.\n"
            "4. Drive your elbows down toward your hips and pull your chest toward the bar.\n"
            "5. Clear the bar with your chin without craning your neck.\n"
            "6. Lower under control over 2-3 seconds to a full hang.\n"
            "7. Keep your ribs down and glutes squeezed to stop the body from swinging."
        ),
        "common_mistakes": (
            "Kipping or swinging to generate momentum; half reps that never reach a full hang; "
            "shrugging the shoulders up at the start; craning the neck to get the chin over the "
            "bar; dropping fast out of the top instead of controlling the descent."
        ),
        "safety_notes": (
            "Build up with band-assisted or eccentric-only reps rather than straining through "
            "failed reps, which strains the elbow and shoulder."
        ),
    },
    {
        "name": "Barbell Bent-Over Row",
        "slug": "barbell-bent-over-row",
        "muscle_group": "Back",
        "secondary_muscles": "Rear Delts, Biceps, Erector Spinae",
        "equipment": "Barbell",
        "mechanic": "compound",
        "difficulty": "intermediate",
        "description": (
            "A horizontal pull performed in a hip-hinged position, building mid-back thickness "
            "and postural strength."
        ),
        "form_instructions": (
            "1. Stand with feet hip-width and grip the bar just outside your knees, overhand.\n"
            "2. Hinge forward to roughly 45 degrees or lower, with a neutral spine and a soft "
            "bend in the knees.\n"
            "3. Let the bar hang at arms' length and brace your core hard.\n"
            "4. Pull the bar toward your lower ribs or upper abdomen, leading with the elbows.\n"
            "5. Squeeze the shoulder blades together at the top for a beat.\n"
            "6. Lower under control to full arm extension without letting your torso rise.\n"
            "7. Keep the torso angle fixed for the whole set."
        ),
        "common_mistakes": (
            "Using the lower back and hips to heave the weight up; standing up progressively as "
            "the set gets hard; rounding the upper back; pulling to the chest instead of the "
            "lower ribs; going so heavy that the range of motion collapses."
        ),
        "safety_notes": (
            "The hinged position loads the lumbar spine isometrically. If your back rounds or "
            "your torso rises, the weight is too heavy."
        ),
    },
    {
        "name": "Romanian Deadlift",
        "slug": "romanian-deadlift",
        "muscle_group": "Hamstrings",
        "secondary_muscles": "Glutes, Erector Spinae, Forearms",
        "equipment": "Barbell",
        "mechanic": "compound",
        "difficulty": "intermediate",
        "description": (
            "A hip-hinge accessory that loads the hamstrings and glutes through a long "
            "eccentric stretch."
        ),
        "form_instructions": (
            "1. Start standing tall holding the bar at hip height with an overhand grip.\n"
            "2. Soften the knees to roughly 15 degrees of bend and hold that angle throughout.\n"
            "3. Brace, then push your hips straight back while keeping the bar in contact with "
            "your thighs.\n"
            "4. Lower until you feel a strong hamstring stretch, usually around mid-shin, "
            "without the lower back rounding.\n"
            "5. Drive the hips forward to return to standing, squeezing the glutes at the top.\n"
            "6. Keep the lats engaged so the bar never drifts forward.\n"
            "7. Control the eccentric for 2-3 seconds - that is where the stimulus is."
        ),
        "common_mistakes": (
            "Turning it into a squat by bending the knees; letting the bar drift away from the "
            "legs; chasing depth past the point where the spine stays neutral; hyperextending "
            "the lower back at lockout."
        ),
        "safety_notes": (
            "Range of motion is dictated by your hamstring flexibility, not by touching the "
            "floor. Stop where your back can stay neutral."
        ),
    },
    {
        "name": "Dumbbell Incline Press",
        "slug": "dumbbell-incline-press",
        "muscle_group": "Chest",
        "secondary_muscles": "Front Delts, Triceps",
        "equipment": "Dumbbell",
        "mechanic": "compound",
        "difficulty": "beginner",
        "description": (
            "An inclined press with dumbbells that biases the upper chest and allows a deeper, "
            "more shoulder-friendly range of motion than a barbell."
        ),
        "form_instructions": (
            "1. Set the bench to 30-45 degrees. Steeper turns it into a shoulder press.\n"
            "2. Sit with the dumbbells resting on your thighs, then kick them up one at a time "
            "as you lie back.\n"
            "3. Retract your shoulder blades and plant your feet.\n"
            "4. Start with the dumbbells just outside your upper chest, palms facing forward or "
            "slightly angled in.\n"
            "5. Press up and slightly inward until the dumbbells are over your upper chest, "
            "stopping just short of clanking them together.\n"
            "6. Lower under control until you feel a stretch across the chest.\n"
            "7. To finish the set, bring the dumbbells to your chest and sit up with them."
        ),
        "common_mistakes": (
            "Setting the incline too steep; flaring the elbows to 90 degrees; bouncing at the "
            "bottom; pressing in an arc so wide the shoulders take over; dropping the dumbbells "
            "carelessly at the end of a set."
        ),
        "safety_notes": (
            "Never let the dumbbells fall behind your shoulders at the bottom - that is the "
            "position where pec and shoulder injuries happen."
        ),
    },
    {
        "name": "Walking Lunge",
        "slug": "walking-lunge",
        "muscle_group": "Legs",
        "secondary_muscles": "Glutes, Hamstrings, Calves, Core",
        "equipment": "Dumbbell",
        "mechanic": "compound",
        "difficulty": "beginner",
        "description": (
            "A single-leg pattern that builds unilateral strength, balance and hip stability "
            "while exposing left-to-right imbalances."
        ),
        "form_instructions": (
            "1. Hold a dumbbell in each hand at your sides, or use bodyweight to start.\n"
            "2. Stand tall with your chest up, shoulders back and core braced.\n"
            "3. Step forward far enough that both knees can reach about 90 degrees.\n"
            "4. Lower straight down until the rear knee is just above the floor.\n"
            "5. Drive through the front heel to bring the rear leg through into the next step.\n"
            "6. Keep the front shin close to vertical and the torso upright.\n"
            "7. Alternate legs for the full distance or rep count."
        ),
        "common_mistakes": (
            "Steps too short, which slams the front knee forward; letting the front knee cave "
            "inward; leaning the torso forward; crashing the back knee into the floor; looking "
            "down, which pulls the chest down with it."
        ),
        "safety_notes": (
            "Master bodyweight lunges before loading them. If your balance breaks down, use "
            "stationary split squats instead."
        ),
    },
    {
        "name": "Cable Face Pull",
        "slug": "cable-face-pull",
        "muscle_group": "Shoulders",
        "secondary_muscles": "Rear Delts, Rhomboids, Mid Traps, Rotator Cuff",
        "equipment": "Cable Machine",
        "mechanic": "isolation",
        "difficulty": "beginner",
        "description": (
            "A rear-delt and upper-back isolation movement widely used to balance out heavy "
            "pressing and support healthy shoulder mechanics."
        ),
        "form_instructions": (
            "1. Attach a rope to a cable set at roughly face or upper-chest height.\n"
            "2. Grip the rope with both palms facing each other, thumbs toward you.\n"
            "3. Step back until the cable is taut with your arms extended, and stagger your "
            "stance for stability.\n"
            "4. Pull the rope toward your face, separating your hands as you go.\n"
            "5. Finish with your hands beside your ears, elbows high and level with your "
            "shoulders, in a 'double biceps' position.\n"
            "6. Squeeze the rear delts and mid-back for a full second.\n"
            "7. Return under control without letting your shoulders roll forward."
        ),
        "common_mistakes": (
            "Loading too heavy so the lats and biceps take over; letting the elbows drop below "
            "shoulder height; leaning back to generate momentum; rushing the reps instead of "
            "pausing at peak contraction."
        ),
        "safety_notes": (
            "This is a light, high-rep movement. Chasing heavy weight here defeats its purpose "
            "and irritates the shoulder."
        ),
    },
]

# ------------------------------------------------------------------------ ped profiles
GENERAL_HARM_REDUCTION = (
    "Non-medical use is not endorsed here. If you are considering or already using this "
    "compound, the single most protective step is working with a physician who knows about it. "
    "Never self-diagnose, never dose based on forum anecdotes, and get baseline bloodwork before "
    "anything else."
)

PED_PROFILES: list[dict] = [
    {
        "name": "Testosterone Enanthate",
        "slug": "testosterone-enanthate",
        "aliases": "Test E",
        "compound_class": "Anabolic-Androgenic Steroid",
        "category": "AAS",
        "administration_route": "Intramuscular injection",
        "half_life": "Approximately 4.5 days",
        "mechanism_of_action": (
            "An esterified form of testosterone. After injection the ester is cleaved and free "
            "testosterone binds the androgen receptor, increasing muscle protein synthesis and "
            "nitrogen retention. It also aromatises to estradiol and converts to DHT."
        ),
        "claimed_effects": (
            "Increased lean mass, strength and recovery capacity; improved libido and mood when "
            "correcting a genuine deficiency."
        ),
        "evidence_summary": (
            "Testosterone replacement therapy is a legitimate, well-studied medical treatment "
            "for diagnosed hypogonadism. Supraphysiological dosing for performance is a "
            "different matter: it reliably increases lean mass, and it reliably increases the "
            "risks described below. Medical evidence supports the treatment, not the "
            "performance use."
        ),
        "cardiovascular_risk": (
            "Suppresses HDL ('good') cholesterol and raises LDL, worsening the atherogenic "
            "profile. Associated with left ventricular hypertrophy, elevated blood pressure, "
            "increased haematocrit and blood viscosity, and a raised risk of thrombosis, "
            "myocardial infarction and stroke. Cardiovascular disease is the leading documented "
            "cause of death among long-term anabolic steroid users."
        ),
        "endocrine_risk": (
            "Shuts down the hypothalamic-pituitary-gonadal axis. Suppresses LH and FSH, halting "
            "natural testosterone production and spermatogenesis. Causes testicular atrophy and "
            "infertility that can persist for a year or more, and sometimes permanently. "
            "Aromatisation to estradiol can cause gynecomastia and water retention."
        ),
        "hepatic_risk": (
            "Injectable testosterone esters bypass first-pass liver metabolism, so direct liver "
            "toxicity is low compared with oral 17-alpha-alkylated steroids. Liver enzymes "
            "should still be monitored, particularly alongside other compounds, and cases of "
            "hepatic strain are documented at high doses."
        ),
        "other_risks": (
            "Acne, accelerated male-pattern baldness in the genetically predisposed, mood "
            "instability and aggression, sleep apnoea, and prostate enlargement. Injection "
            "carries risks of infection, abscess and nerve damage."
        ),
        "legal_status": (
            "A controlled substance in most countries, including Schedule III in the United "
            "States and Class C in the United Kingdom. Legal only with a valid prescription; "
            "supply without one is a criminal offence in many jurisdictions."
        ),
        "medical_supervision_required": True,
        "harm_reduction_notes": GENERAL_HARM_REDUCTION,
        "monitoring_bloodwork": (
            "Baseline and periodic: total and free testosterone, estradiol (sensitive assay), "
            "LH, FSH, full lipid panel, complete blood count with haematocrit, liver panel "
            "(ALT/AST), PSA where age-appropriate, and blood pressure at every check."
        ),
    },
    {
        "name": "Nandrolone Decanoate",
        "slug": "nandrolone-decanoate",
        "aliases": "Deca-Durabolin, Deca",
        "compound_class": "Anabolic-Androgenic Steroid (19-nor)",
        "category": "AAS",
        "administration_route": "Intramuscular injection",
        "half_life": "Approximately 6-12 days",
        "mechanism_of_action": (
            "A 19-nortestosterone derivative with high anabolic and comparatively lower "
            "androgenic activity. It is reduced by 5-alpha-reductase to the weaker DHN rather "
            "than to DHT, and is also a progestin receptor agonist."
        ),
        "claimed_effects": (
            "Lean mass gain, increased collagen synthesis and reported joint comfort, and "
            "improved nitrogen retention."
        ),
        "evidence_summary": (
            "Studied medically for anaemia of renal disease, HIV-associated wasting and severe "
            "osteoporosis. Its performance reputation for 'joint relief' is largely anecdotal "
            "and may reflect fluid retention masking symptoms rather than healing tissue."
        ),
        "cardiovascular_risk": (
            "Markedly suppresses HDL cholesterol, in several reports more severely than "
            "testosterone. Raises blood pressure through fluid retention and is linked to "
            "cardiac remodelling and left ventricular dysfunction in animal and human data."
        ),
        "endocrine_risk": (
            "Profound and long-lasting HPG axis suppression - recovery is typically slower than "
            "with testosterone. Strong progestogenic activity raises prolactin, which can cause "
            "gynecomastia, lactation and the well-documented erectile dysfunction commonly "
            "called 'deca dick'. Suppresses spermatogenesis."
        ),
        "hepatic_risk": (
            "As an injectable ester it is not 17-alpha-alkylated, so hepatotoxicity is lower "
            "than with oral steroids. Elevated liver enzymes and, rarely, peliosis hepatis have "
            "still been reported with nandrolone use, so liver monitoring remains necessary."
        ),
        "other_risks": (
            "Detectable in doping tests for many months. Mood disturbance, sedation, and "
            "persistent sexual dysfunction that can outlast the cycle."
        ),
        "legal_status": (
            "Controlled: Schedule III in the United States, Class C in the United Kingdom. "
            "Prescription-only where available at all."
        ),
        "medical_supervision_required": True,
        "harm_reduction_notes": GENERAL_HARM_REDUCTION,
        "monitoring_bloodwork": (
            "Prolactin and estradiol alongside the standard panel: testosterone, LH, FSH, full "
            "lipids, CBC with haematocrit, liver panel, and blood pressure."
        ),
    },
    {
        "name": "Oxandrolone",
        "slug": "oxandrolone",
        "aliases": "Anavar, Var",
        "compound_class": "Oral Anabolic-Androgenic Steroid (17-alpha-alkylated)",
        "category": "AAS",
        "administration_route": "Oral",
        "half_life": "Approximately 8-10 hours",
        "mechanism_of_action": (
            "A DHT-derived oral steroid, 17-alpha-alkylated so it survives first-pass liver "
            "metabolism. Binds the androgen receptor with low androgenic activity relative to "
            "its anabolic effect, and does not aromatise."
        ),
        "claimed_effects": (
            "Modest lean mass retention, strength gain without significant water retention, and "
            "a reputation as a 'mild' compound."
        ),
        "evidence_summary": (
            "Genuinely FDA-approved for weight regain after severe trauma, burns and chronic "
            "infection, and studied in Turner syndrome. Its 'mild' reputation refers to "
            "androgenic side effects like acne and hair loss - it is not mild on lipids or on "
            "the liver, and that distinction is widely misunderstood."
        ),
        "cardiovascular_risk": (
            "Among the most aggressive suppressors of HDL cholesterol of any commonly used "
            "steroid - studies document HDL reductions of 30-50 percent at therapeutic doses. "
            "This unfavourable lipid shift meaningfully raises cardiovascular risk despite the "
            "compound's reputation for being gentle."
        ),
        "endocrine_risk": (
            "Suppresses endogenous testosterone production even at low doses; suppression is "
            "dose-dependent and real, not absent. Reduces SHBG, altering free hormone levels. "
            "In women, virilisation - deepened voice, clitoral enlargement, facial hair - can "
            "be irreversible."
        ),
        "hepatic_risk": (
            "17-alpha-alkylation makes it directly hepatotoxic. Documented risks include "
            "cholestatic jaundice, elevated transaminases, peliosis hepatis (blood-filled liver "
            "cysts) and, rarely, hepatic tumours. Risk climbs with dose and duration. Note that "
            "creatine kinase and liver enzyme elevations from training can confound testing."
        ),
        "other_risks": (
            "Frequently counterfeited - products sold as oxandrolone often contain other, "
            "harsher compounds entirely. Appetite suppression and mood changes are reported."
        ),
        "legal_status": (
            "Schedule III controlled substance in the United States; prescription-only "
            "elsewhere. Non-medical possession and supply are unlawful in many jurisdictions."
        ),
        "medical_supervision_required": True,
        "harm_reduction_notes": GENERAL_HARM_REDUCTION,
        "monitoring_bloodwork": (
            "Liver panel (ALT, AST, GGT, bilirubin) before, during and after; full lipid panel "
            "with special attention to HDL; testosterone, LH, FSH; CBC; blood pressure."
        ),
    },
    {
        "name": "Stanozolol",
        "slug": "stanozolol",
        "aliases": "Winstrol, Winny",
        "compound_class": "Oral/Injectable Anabolic-Androgenic Steroid (17-alpha-alkylated)",
        "category": "AAS",
        "administration_route": "Oral or intramuscular injection",
        "half_life": "Approximately 9 hours oral, 24 hours injectable",
        "mechanism_of_action": (
            "A DHT-derived, 17-alpha-alkylated steroid. Both the oral and injectable forms are "
            "alkylated. It does not aromatise and strongly lowers SHBG, raising free "
            "testosterone levels."
        ),
        "claimed_effects": (
            "Strength and speed gains without weight gain, a 'dry' or hardened appearance, and "
            "reduced water retention."
        ),
        "evidence_summary": (
            "Medically used for hereditary angioedema and some anaemias. It is one of the most "
            "frequently detected compounds in doping cases. Its cosmetic 'dry look' comes from "
            "the absence of water retention, not from fat loss."
        ),
        "cardiovascular_risk": (
            "Severely suppresses HDL cholesterol and raises LDL - among the worst lipid "
            "profiles of any anabolic steroid. Associated with hypertension, left ventricular "
            "hypertrophy and increased cardiovascular event risk."
        ),
        "endocrine_risk": (
            "Strongly suppresses the HPG axis and endogenous testosterone. Sharply lowers SHBG, "
            "distorting hormone panels. High virilisation risk in women, including irreversible "
            "voice deepening."
        ),
        "hepatic_risk": (
            "Notably hepatotoxic. Because both oral and injectable forms are 17-alpha-alkylated, "
            "switching to injection does not spare the liver - a widespread and dangerous "
            "misconception. Documented cases of cholestatic hepatitis, jaundice, peliosis "
            "hepatis and hepatic adenoma."
        ),
        "other_risks": (
            "Frequently reported joint pain and dryness, tendon stiffness with an associated "
            "rupture risk, acne and accelerated hair loss."
        ),
        "legal_status": (
            "Schedule III in the United States, Class C in the United Kingdom. Banned by WADA "
            "and every major sporting body."
        ),
        "medical_supervision_required": True,
        "harm_reduction_notes": GENERAL_HARM_REDUCTION,
        "monitoring_bloodwork": (
            "Frequent liver panels are essential; full lipid panel; testosterone, LH, FSH, SHBG; "
            "CBC; blood pressure at every check."
        ),
    },
    {
        "name": "Trenbolone Acetate",
        "slug": "trenbolone-acetate",
        "aliases": "Tren A",
        "compound_class": "Anabolic-Androgenic Steroid (19-nor)",
        "category": "AAS",
        "administration_route": "Intramuscular injection",
        "half_life": "Approximately 1-3 days",
        "mechanism_of_action": (
            "An extremely potent 19-nor androgen receptor agonist with roughly five times the "
            "anabolic and androgenic rating of testosterone. It does not aromatise but is a "
            "progestin receptor agonist. Originally a veterinary cattle-implant compound."
        ),
        "claimed_effects": (
            "Rapid strength and lean mass gain with simultaneous fat loss and a hard, dry "
            "appearance."
        ),
        "evidence_summary": (
            "There is no human medical use and therefore no human safety data. Everything known "
            "about its effects in people comes from veterinary pharmacology and user reports. "
            "It is widely regarded, including among people who use steroids, as one of the most "
            "dangerous compounds in circulation."
        ),
        "cardiovascular_risk": (
            "Devastating effect on lipids - can crash HDL to near-undetectable levels. Strongly "
            "associated with hypertension, tachycardia, cardiac hypertrophy and severely reduced "
            "cardiovascular endurance. Users commonly report breathlessness during light "
            "activity, a direct sign of cardiac and pulmonary strain."
        ),
        "endocrine_risk": (
            "Causes among the most severe and prolonged HPG axis shutdowns of any compound. "
            "Progestogenic activity raises prolactin, causing gynecomastia, lactation and sexual "
            "dysfunction. Recovery of natural production is often slow and sometimes incomplete."
        ),
        "hepatic_risk": (
            "Not 17-alpha-alkylated, so it is not classically hepatotoxic. However, "
            "significantly elevated liver and kidney markers are commonly reported, and "
            "trenbolone is strongly associated with nephrotoxicity - kidney damage - which is "
            "an under-appreciated organ risk with this compound."
        ),
        "other_risks": (
            "Severe insomnia, night sweats, anxiety, paranoia and aggression are widely and "
            "consistently reported. Persistent cough on injection. Marked appetite changes."
        ),
        "legal_status": (
            "Schedule III in the United States. No human prescription exists anywhere, so all "
            "human-use product is either veterinary or illicitly manufactured."
        ),
        "medical_supervision_required": True,
        "harm_reduction_notes": (
            GENERAL_HARM_REDUCTION
            + " There is no human safety data for this compound at all - a physician cannot "
            "make it safe, only less unmonitored."
        ),
        "monitoring_bloodwork": (
            "Full lipid panel, prolactin, kidney function (creatinine, eGFR, cystatin C), liver "
            "panel, CBC with haematocrit, blood pressure, and resting heart rate."
        ),
    },
    {
        "name": "Human Growth Hormone",
        "slug": "human-growth-hormone",
        "aliases": "HGH, Somatropin",
        "compound_class": "Recombinant Peptide Hormone",
        "category": "Peptide Hormone",
        "administration_route": "Subcutaneous injection",
        "half_life": "Approximately 2-3 hours (biological effect far longer via IGF-1)",
        "mechanism_of_action": (
            "Recombinant human growth hormone binds hepatic and peripheral GH receptors, driving "
            "IGF-1 production. IGF-1 mediates most of the anabolic and growth-promoting effects, "
            "including cellular proliferation and lipolysis."
        ),
        "claimed_effects": (
            "Fat loss, improved recovery and sleep quality, better skin and connective tissue, "
            "and modest lean mass increase."
        ),
        "evidence_summary": (
            "A legitimate treatment for diagnosed GH deficiency, Turner syndrome and a few other "
            "conditions. In healthy adults the evidence for performance benefit is weak: "
            "controlled studies show increased lean body mass driven substantially by fluid "
            "retention, with little to no measurable improvement in strength or exercise "
            "capacity. The anti-ageing marketing is not supported by evidence."
        ),
        "cardiovascular_risk": (
            "Chronic excess causes cardiac hypertrophy and cardiomyopathy - the same process "
            "seen in acromegaly. Fluid retention raises blood pressure. Long-term GH excess is "
            "associated with substantially increased cardiovascular mortality."
        ),
        "endocrine_risk": (
            "Causes insulin resistance and can precipitate type 2 diabetes; this is one of the "
            "most consistent and serious findings. Suppresses natural GH secretion. Can disturb "
            "thyroid function and cortisol metabolism. In excess it produces acromegaly: "
            "irreversible enlargement of the jaw, brow, hands, feet and internal organs."
        ),
        "hepatic_risk": (
            "The liver is the principal site of IGF-1 production and bears the metabolic load. "
            "GH excess alters hepatic glucose handling and is linked to non-alcoholic fatty "
            "liver disease. Liver function must be monitored, particularly given the diabetes "
            "risk."
        ),
        "other_risks": (
            "Carpal tunnel syndrome, joint and muscle pain, oedema. A theoretical but seriously "
            "considered concern that IGF-1 elevation may promote growth of existing tumours."
        ),
        "legal_status": (
            "Prescription-only worldwide. In the United States, distributing HGH for "
            "non-medical or performance purposes is a specific federal felony under 21 U.S.C. "
            "333(e) - a stricter rule than for most other substances here."
        ),
        "medical_supervision_required": True,
        "harm_reduction_notes": GENERAL_HARM_REDUCTION,
        "monitoring_bloodwork": (
            "IGF-1, fasting glucose, fasting insulin and HbA1c (essential given the diabetes "
            "risk), thyroid panel, liver panel, lipids, and blood pressure."
        ),
    },
    {
        "name": "Ipamorelin",
        "slug": "ipamorelin",
        "aliases": "NNC 26-0161",
        "compound_class": "Growth Hormone Secretagogue (GHRP)",
        "category": "Peptide",
        "administration_route": "Subcutaneous injection",
        "half_life": "Approximately 2 hours",
        "mechanism_of_action": (
            "A selective ghrelin receptor (GHS-R1a) agonist that stimulates the pituitary to "
            "release growth hormone in a pulsatile pattern. Its selectivity means it has "
            "comparatively little effect on cortisol and prolactin compared with older GHRPs."
        ),
        "claimed_effects": (
            "Increased natural GH pulses, improved sleep and recovery, and modest body "
            "composition changes without the appetite spike of other secretagogues."
        ),
        "evidence_summary": (
            "Studied in early-phase clinical trials, including for post-operative ileus, but "
            "never approved for any human indication. Long-term human safety data does not "
            "exist. It is sold as a research chemical, and its risks are best understood as the "
            "risks of chronically elevated GH."
        ),
        "cardiovascular_risk": (
            "By raising GH and IGF-1 it carries the same cardiovascular concerns as GH itself: "
            "cardiac hypertrophy with sustained elevation, fluid retention and raised blood "
            "pressure. Long-term cardiovascular safety in humans is entirely unstudied."
        ),
        "endocrine_risk": (
            "Directly manipulates the pituitary GH axis. Chronic use can blunt natural GH "
            "secretion. Elevated GH and IGF-1 impair insulin sensitivity and raise blood "
            "glucose. Sustained use risks the same acromegaly-spectrum changes as exogenous GH."
        ),
        "hepatic_risk": (
            "GH-driven IGF-1 production loads the liver, and the associated insulin resistance "
            "is a risk factor for fatty liver disease. Additionally, research-chemical peptides "
            "are unregulated: purity, sterility and actual contents are unverified, which adds "
            "an unquantified hepatic and systemic risk from contaminants."
        ),
        "other_risks": (
            "Injection site reactions, headache, water retention, transient dizziness. Because "
            "products are unregulated, what is in the vial may not be what is on the label."
        ),
        "legal_status": (
            "Not approved for human use in the United States, EU or UK. Sold only as a 'research "
            "chemical, not for human consumption'. Banned by WADA."
        ),
        "medical_supervision_required": True,
        "harm_reduction_notes": GENERAL_HARM_REDUCTION,
        "monitoring_bloodwork": (
            "IGF-1, fasting glucose and HbA1c, insulin, prolactin and cortisol at baseline, "
            "liver panel, lipids, and blood pressure."
        ),
    },
    {
        "name": "CJC-1295",
        "slug": "cjc-1295",
        "aliases": "Modified GRF (1-29), CJC-1295 DAC",
        "compound_class": "Growth Hormone Releasing Hormone Analogue",
        "category": "Peptide",
        "administration_route": "Subcutaneous injection",
        "half_life": "Approximately 30 minutes without DAC; up to 6-8 days with DAC",
        "mechanism_of_action": (
            "A synthetic analogue of GHRH that binds pituitary GHRH receptors to stimulate GH "
            "release. The DAC (Drug Affinity Complex) version binds serum albumin, extending its "
            "half-life to days and producing a sustained 'bleed' of GH rather than natural "
            "pulses."
        ),
        "claimed_effects": (
            "Elevated GH and IGF-1, improved recovery and sleep, and fat loss. Often stacked "
            "with a GHRP such as ipamorelin."
        ),
        "evidence_summary": (
            "Reached phase II trials and was discontinued. It is not approved anywhere for human "
            "use, and there is no long-term human safety data. The DAC version's continuous "
            "release is a particular concern because it overrides the body's natural pulsatile "
            "GH rhythm, which is itself thought to be physiologically important."
        ),
        "cardiovascular_risk": (
            "Sustained GH and IGF-1 elevation carries the documented GH-excess cardiovascular "
            "profile: cardiac hypertrophy, cardiomyopathy risk with chronic use, fluid retention "
            "and hypertension. The DAC version's continuous elevation may amplify this compared "
            "with pulsatile alternatives."
        ),
        "endocrine_risk": (
            "Continuous GHRH receptor stimulation can desensitise the pituitary and disrupt the "
            "natural GH rhythm. Raises blood glucose and impairs insulin sensitivity. Chronic "
            "excess risks acromegalic changes, which are largely irreversible."
        ),
        "hepatic_risk": (
            "Hepatic IGF-1 output rises under sustained GH stimulation, and the resulting "
            "insulin resistance is a driver of fatty liver disease. As an unregulated research "
            "chemical, contamination and mislabelling add unquantified hepatic risk."
        ),
        "other_risks": (
            "Injection site reactions, flushing, headache, numbness or tingling. Reported "
            "potential for antibody formation against the peptide."
        ),
        "legal_status": (
            "Not approved for human use in any major jurisdiction. Sold as a research chemical. "
            "Prohibited by WADA at all times."
        ),
        "medical_supervision_required": True,
        "harm_reduction_notes": GENERAL_HARM_REDUCTION,
        "monitoring_bloodwork": (
            "IGF-1, fasting glucose, HbA1c, insulin, full thyroid panel, liver panel, lipids, "
            "and blood pressure."
        ),
    },
    {
        "name": "BPC-157",
        "slug": "bpc-157",
        "aliases": "Body Protection Compound 157, Pentadecapeptide BPC 157",
        "compound_class": "Synthetic Pentadecapeptide",
        "category": "Peptide",
        "administration_route": "Subcutaneous or oral (both unapproved)",
        "half_life": "Poorly characterised in humans; estimated to be short",
        "mechanism_of_action": (
            "A synthetic 15-amino-acid sequence derived from a protein found in gastric juice. "
            "Animal studies suggest it promotes angiogenesis, upregulates growth factor "
            "receptors and modulates the nitric oxide pathway, which is the proposed basis for "
            "its tissue-repair claims."
        ),
        "claimed_effects": (
            "Accelerated healing of tendon, ligament, muscle and gut tissue; reduced "
            "inflammation; protection against NSAID-induced gut damage."
        ),
        "evidence_summary": (
            "This is the critical point: essentially all supporting evidence comes from rodent "
            "studies. There are no completed, peer-reviewed, controlled human trials "
            "establishing either efficacy or safety. Popular claims about its healing power are "
            "extrapolated from animals to humans without justification. The FDA moved it to the "
            "category of substances barred from compounding in 2023, citing insufficient safety "
            "data."
        ),
        "cardiovascular_risk": (
            "Human cardiovascular effects are unknown - which is a risk, not a reassurance. Its "
            "proposed angiogenic (blood-vessel-forming) mechanism is precisely the mechanism "
            "that raises theoretical concern about promoting vascular growth in unwanted places, "
            "including tumours. No human cardiovascular safety data exists."
        ),
        "endocrine_risk": (
            "No established direct hormonal mechanism, but its effects on human endocrine "
            "function have never been systematically studied. Animal work suggests interaction "
            "with growth factor and dopaminergic systems whose downstream endocrine consequences "
            "in humans are entirely uncharacterised."
        ),
        "hepatic_risk": (
            "Human hepatic safety is unstudied. Some rodent research suggests hepatoprotective "
            "effects, but this has never been confirmed in humans and must not be read as a "
            "guarantee of liver safety. A significant practical risk is that unregulated "
            "products contain solvents, endotoxins or incorrect compounds that the liver must "
            "process."
        ),
        "other_risks": (
            "The dominant risk here is the unregulated grey market: no purity standards, no "
            "sterility guarantees, no dosing standards. Independent testing has repeatedly found "
            "research peptides that are underdosed, mislabelled or contaminated."
        ),
        "legal_status": (
            "Not approved for human use anywhere. Placed on the FDA's Category 2 bulk substances "
            "list in 2023, effectively barring compounding pharmacies from preparing it. Banned "
            "by WADA since 2022. Sold only as a research chemical."
        ),
        "medical_supervision_required": True,
        "harm_reduction_notes": (
            GENERAL_HARM_REDUCTION
            + " Be especially sceptical of confident claims about this compound - the confidence "
            "in marketing far exceeds the evidence in the literature."
        ),
        "monitoring_bloodwork": (
            "No established monitoring protocol exists. A sensible baseline would include liver "
            "and kidney panels, CBC and inflammatory markers, but no protocol is validated."
        ),
    },
    {
        "name": "Clenbuterol",
        "slug": "clenbuterol",
        "aliases": "Clen",
        "compound_class": "Beta-2 Adrenergic Agonist",
        "category": "Stimulant / Beta-Agonist",
        "administration_route": "Oral",
        "half_life": "Approximately 26-36 hours",
        "mechanism_of_action": (
            "A long-acting selective beta-2 adrenergic receptor agonist. It raises cyclic AMP, "
            "increasing lipolysis, metabolic rate and core temperature. It is a bronchodilator, "
            "not an anabolic steroid, though it is often grouped with them."
        ),
        "claimed_effects": (
            "Fat loss, appetite suppression, and a claimed muscle-sparing effect during a "
            "calorie deficit."
        ),
        "evidence_summary": (
            "Approved in some countries as a veterinary and human bronchodilator, but not "
            "approved for human use in the United States. The anabolic and muscle-sparing "
            "effects demonstrated in livestock have not been reproduced meaningfully in humans. "
            "Its fat-loss effect is real but modest and short-lived as receptors downregulate."
        ),
        "cardiovascular_risk": (
            "This is the primary danger. Causes tachycardia, palpitations, arrhythmias and "
            "raised blood pressure. Documented cases of myocardial infarction, atrial "
            "fibrillation and cardiac arrest, including in young, otherwise healthy users. "
            "Animal studies show it causes cardiac hypertrophy with collagen deposition - "
            "structural heart damage, not beneficial growth. Overdose cases regularly result in "
            "hospital admission."
        ),
        "endocrine_risk": (
            "Not a hormone and it does not suppress the HPG axis. It does disrupt metabolic and "
            "adrenergic regulation, causing insulin resistance and significant potassium and "
            "magnesium depletion - electrolyte disturbances that themselves trigger dangerous "
            "arrhythmias. Sustained adrenergic stimulation places chronic stress on the "
            "adrenal-sympathetic system."
        ),
        "hepatic_risk": (
            "Not classically hepatotoxic, but elevated liver enzymes are reported in overdose "
            "and poisoning cases. A major documented hazard is contaminated meat and illicit "
            "product causing clenbuterol poisoning outbreaks, which present with systemic "
            "toxicity including hepatic strain."
        ),
        "other_risks": (
            "Severe muscle cramps from taurine and electrolyte depletion, persistent tremor, "
            "insomnia, anxiety, sweating and headaches. The long half-life means side effects "
            "accumulate and persist well after the last dose."
        ),
        "legal_status": (
            "Not approved for human use in the United States and illegal to market for weight "
            "loss or bodybuilding. Prescription-only where approved. Banned by WADA at all "
            "times, in and out of competition."
        ),
        "medical_supervision_required": True,
        "harm_reduction_notes": (
            GENERAL_HARM_REDUCTION
            + " Cardiac symptoms - chest pain, fainting, a racing or irregular heartbeat - are "
            "an emergency, not a side effect to push through. Seek immediate medical care."
        ),
        "monitoring_bloodwork": (
            "ECG and blood pressure monitoring are more important here than bloodwork. Also "
            "check electrolytes (potassium, magnesium), fasting glucose, liver panel and "
            "resting heart rate."
        ),
    },
]


def _upsert(session, model, rows: list[dict]) -> tuple[int, int]:
    created = updated = 0
    for row in rows:
        existing = session.scalar(select(model).where(model.slug == row["slug"]))
        if existing is None:
            session.add(model(**row))
            created += 1
        else:
            for key, value in row.items():
                setattr(existing, key, value)
            updated += 1
    return created, updated


def seed(reset: bool = False) -> None:
    if reset:
        print("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)

    init_db()
    print("Tables ready.")

    with SessionLocal() as session:
        ex_created, ex_updated = _upsert(session, Exercise, EXERCISES)
        ped_created, ped_updated = _upsert(session, PEDProfile, PED_PROFILES)
        session.commit()

    print(f"Exercises:    {ex_created} created, {ex_updated} updated (total {len(EXERCISES)})")
    print(f"PED profiles: {ped_created} created, {ped_updated} updated (total {len(PED_PROFILES)})")
    print("Seeding complete.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed the Vanguard Fitness database.")
    parser.add_argument(
        "--reset", action="store_true", help="Drop and recreate all tables before seeding."
    )
    args = parser.parse_args()

    try:
        seed(reset=args.reset)
    except Exception as exc:  # noqa: BLE001 - top-level CLI guard
        print(f"Seeding failed: {exc}", file=sys.stderr)
        print(
            "\nCheck that the database is reachable. Set VANGUARD_USE_SQLITE=true to seed a "
            "local SQLite file instead of SQL Server.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
