"""
Fixtures for the Phase 0 shadow prototype harness.

BRANDON is the verbatim canonical fixture (same text as
backend/tests/test_brandon_grounding_regression.py and
backend/scripts/audit_repeatability.py's "brandon_grounding" fixture),
reshaped into LifeSourceData with background/caregiver_history/temperament
split the same way the real production UI splits them into three fields.

COMPLEX, MIXED, and LOW_ADVERSITY are original, clearly-synthetic test
personas (not based on any real person) constructed for this prototype only,
to exercise different life shapes:
  - COMPLEX: many experiences (16), multiple concurrent life threads.
  - MIXED: moderate adversity + moderate protection, mid-size (9 experiences).
  - LOW_ADVERSITY: stable life (7 experiences) that should legitimately
    produce few or no significant patterns/hypotheses - a true-negative
    case the engine must handle without inventing problems.

Each fixture also carries SELF_EVENT_IDS (used by the regression checker,
not the generic validator) - the experience ids whose subject is the
persona's own behavior, for the hard caregiver/self-confusion check.
"""
from app.services.whole_life_formulation.request_assembler import ExperienceSource, LifeSourceData


def _exp(id_, age, seq, text):
    return ExperienceSource(id=id_, age_at_event=age, sequence_index=seq, user_description=text)


# ---------------------------------------------------------------------------
# BRANDON - verbatim canonical fixture
# ---------------------------------------------------------------------------

BRANDON = LifeSourceData(
    persona_name="Brandon Vasquez",
    current_age=40,
    background=(
        "Brandon was born in St. Louis in 1980 and placed for adoption as an infant. He was adopted "
        "into a large foster/adoptive family in San Diego and was the youngest of eight adopted "
        "children. He spent parts of childhood in San Diego, England, and Benson, Arizona, moving "
        "several times before returning to San Diego at 15. His childhood included travel, books, "
        "science, music, art, church, large groups of friends, and later significant involvement with "
        "drugs, nightlife, photography, treatment work, and AI development."
    ),
    caregiver_history=(
        "His biological mother was a young woman in St. Louis who placed him for adoption; he does not "
        "remember her. He was raised by Audrey, an older British woman who had operated a foster home "
        "and later adopted eight children. He describes her as loving, generous, cultured, and largely "
        "without discipline. Audrey died when Brandon was 15. He was then adopted by Karen, who tried "
        "to provide structure, counseling, and treatment during his teenage years and is the woman he "
        "calls his mother today."
    ),
    temperament_self_description=(
        "As a child, Brandon describes himself as angry, rebellious, and sometimes emotionally shut "
        "off. He also describes himself as outgoing, extroverted, socially confident, fearless, "
        "creative, and able to make friends easily. He was drawn to literature, science, music, art, "
        "leadership, and protecting people he felt could not protect themselves."
    ),
    experiences=[
        _exp("brandon_e01", 4, 1, "Brandon is placed for adoption in St. Louis and adopted into Audrey's foster family in San Diego."),
        _exp("brandon_e02", 6, 1, "Audrey takes Brandon to live in England, where he attends primary school, travels extensively with her, and spends time with her British relatives."),
        _exp("brandon_e03", 12, 1, "Brandon moves to Benson, Arizona, where he forms close friendships and begins getting into trouble."),
        _exp("brandon_e04", 14, 1, "He becomes deeply involved in a church in Benson. A pastor trains him as a youth minister, and the youth group becomes a major part of his life."),
        _exp("brandon_e05", 15, 1, "Audrey dies. Brandon gives up his involvement with the church and begins moving heavily into crime and drugs"),
        _exp("brandon_e06", 16, 1, "Brandon enters a serious relationship with Heather. She later becomes pregnant with his son while Brandon is becoming heavily involved with drugs"),
        _exp("brandon_e07", 19, 1, "While incarcerated, Brandon meets a man who teaches him event promotion. After release, Karen allows him to handle entertainment at her bar, leading to years of promoting bands, art shows, fashion shows, fundraisers, and nightclub events."),
        _exp("brandon_e08", 23, 1, "A model named Soma buys Brandon his first camera. He moves to Los Angeles and begins a freelance photography career that lasts roughly 20 years, including magazine publication and travel across the country"),
        _exp("brandon_e09", 37, 1, "Brandon meets Hillary, whom he describes as the most significant romantic relationship of his life. Their relationship lasts roughly two years before she relapses and dies from alcohol use."),
        _exp("brandon_e10", 40, 1, "After another prolonged period of drug use, Brandon enters rehab, earns his RADT, becomes a case manager in substance-use treatment, and begins developing AI applications."),
    ],
)

# The two experiences a naive keyword/subject-blind extractor has historically
# mis-attributed to a caregiver (the exact regression this whole system exists
# to prevent). Both describe BRANDON'S OWN substance use / incarceration.
BRANDON_SELF_EVENT_IDS = {"brandon_e10", "brandon_e07"}


# ---------------------------------------------------------------------------
# COMPLEX - many experiences, multiple concurrent threads
# ---------------------------------------------------------------------------

COMPLEX = LifeSourceData(
    persona_name="Test Subject Complex",
    current_age=52,
    background=(
        "Subject was born in Detroit to two working-class parents who remained married throughout "
        "childhood. The household included three siblings across a twelve-year span. The family moved "
        "twice for the father's factory work but stayed within the same metro area. Subject describes "
        "a home life that was financially tight but stable, with periodic tension between the parents "
        "over money that never escalated to violence."
    ),
    caregiver_history=(
        "Mother worked nights as a nurse and was often exhausted but consistently present for meals and "
        "school events. Father worked long factory shifts and was emotionally reserved, showing "
        "affection mainly through providing rather than words. An older aunt lived nearby and became a "
        "significant secondary caregiver, particularly during mother's night shifts, and is described "
        "as warm and talkative in a way the parents were not."
    ),
    temperament_self_description=(
        "Subject describes being a watchful, methodical child, more comfortable with structure than "
        "spontaneity, and slow to trust new people but fiercely loyal once trust was established. "
        "Subject also describes a strong competitive streak and a lifelong tendency to over-prepare for "
        "anything that felt uncertain."
    ),
    experiences=[
        _exp("cx_e01", 5, 1, "Subject starts kindergarten and cries every morning for the first month, refusing to be left; the aunt begins walking Subject to school to ease the transition."),
        _exp("cx_e02", 8, 1, "The family's second move disrupts Subject's only close friendship at the time; Subject describes feeling like an outsider at the new school for most of that year."),
        _exp("cx_e03", 10, 1, "Subject's aunt is diagnosed with breast cancer and undergoes a difficult year of treatment; Subject spends many afternoons at the hospital."),
        _exp("cx_e04", 11, 1, "The aunt recovers fully. Subject describes this as the first time Subject understood that frightening things could turn out okay."),
        _exp("cx_e05", 13, 1, "Subject joins the middle school debate team on a teacher's suggestion and unexpectedly excels, winning a regional competition within the first year."),
        _exp("cx_e06", 15, 1, "A parental argument over medical bills escalates into a week of the parents barely speaking; Subject describes feeling responsible for keeping siblings calm during this period."),
        _exp("cx_e07", 17, 1, "Subject is accepted to a competitive out-of-state university on a partial scholarship, the first in the family to leave the state for college."),
        _exp("cx_e08", 19, 1, "Subject's first serious college relationship ends when the partner cheats; Subject describes becoming noticeably more guarded in relationships afterward."),
        _exp("cx_e09", 22, 1, "Subject graduates with honors and takes an entry-level engineering job in a new city, knowing no one there."),
        _exp("cx_e10", 24, 1, "Subject is laid off during a company-wide restructuring eight months into the job; re-employment takes five months and depletes most of Subject's savings."),
        _exp("cx_e11", 26, 1, "Subject meets a partner through a mutual friend; the relationship is described as steady and low-drama from early on."),
        _exp("cx_e12", 29, 1, "Subject and partner marry in a small ceremony; Subject describes feeling surprised by how easy it was to trust this particular person."),
        _exp("cx_e13", 31, 1, "Subject's father has a serious heart attack and survives; Subject flies home repeatedly over several months to help coordinate his care."),
        _exp("cx_e14", 34, 1, "Subject is promoted into a management role for the first time and describes early months as stressful, overpreparing for every meeting."),
        _exp("cx_e15", 41, 1, "Subject's mother dies after a short illness; Subject describes the grief as intense but says the extended family's support made it bearable."),
        _exp("cx_e16", 48, 1, "Subject begins volunteering as a mentor for first-generation college students, describing it as wanting to give someone else the preparation Subject had to build alone."),
    ],
)


# ---------------------------------------------------------------------------
# MIXED - moderate adversity + moderate protection
# ---------------------------------------------------------------------------

MIXED = LifeSourceData(
    persona_name="Test Subject Mixed",
    current_age=33,
    background=(
        "Subject grew up in a mid-sized suburb, raised primarily by a single mother after the parents "
        "separated when Subject was four. Subject describes the early separation as confusing but says "
        "contact with the father continued on and off through adolescence. Financial strain was a "
        "recurring theme, and the family moved apartments three times before Subject turned twelve."
    ),
    caregiver_history=(
        "Mother worked two jobs for several years and was often stretched thin, sometimes short-tempered "
        "when exhausted, but Subject describes her as reliably present at the end of each day regardless "
        "of how hard the day had been. The father, when present, was fun and affectionate but "
        "unpredictable about visits, sometimes missing planned weekends without explanation."
    ),
    temperament_self_description=(
        "Subject describes being an easily excitable, socially eager child who sought approval from "
        "adults, coupled with a persistent worry about being forgotten or left out. Subject also "
        "describes a strong sense of humor used, in Subject's own words, 'to keep things light so people "
        "wouldn't leave.'"
    ),
    experiences=[
        _exp("mx_e01", 4, 1, "Subject's parents separate. Subject is told mother and father will live in different houses now but continue to see him."),
        _exp("mx_e02", 7, 1, "Father misses a planned birthday visit without calling; Subject waits by the window for several hours before mother explains he isn't coming."),
        _exp("mx_e03", 9, 1, "Subject's grandmother begins picking Subject up from school two days a week while mother works a second shift, and Subject describes these afternoons as the calmest part of the week."),
        _exp("mx_e04", 12, 1, "Subject is bullied for several months over hand-me-down clothes; a teacher intervenes after noticing Subject withdrawing in class."),
        _exp("mx_e05", 14, 1, "Subject joins the school theater program and describes finally feeling 'good at being seen' after years of feeling overlooked."),
        _exp("mx_e06", 17, 1, "Father misses Subject's high school graduation; Subject describes deciding that day to stop expecting him to show up for anything."),
        _exp("mx_e07", 20, 1, "Subject enters a relationship in college that a close friend describes as one-sided; Subject stays in it for two years despite repeated disappointments."),
        _exp("mx_e08", 22, 1, "Subject ends the relationship after the friend's continued concern, and describes it afterward as 'finally believing I deserved better.'"),
        _exp("mx_e09", 28, 1, "Subject starts a small business with a close friend from the theater program; Subject describes the partnership as the most stable working relationship of Subject's life so far."),
    ],
)


# ---------------------------------------------------------------------------
# LOW_ADVERSITY - stable life; true-negative case
# ---------------------------------------------------------------------------

LOW_ADVERSITY = LifeSourceData(
    persona_name="Test Subject Stable",
    current_age=29,
    background=(
        "Subject was raised in the same house from birth through college by two married parents in a "
        "small college town. The family was financially comfortable and Subject describes childhood as "
        "unremarkable in a positive sense - routine, predictable, and without major disruption."
    ),
    caregiver_history=(
        "Both parents were consistently present and are described as warm, calm, and even-tempered. "
        "Neither parent worked unusual hours; family dinners together were the norm rather than the "
        "exception. Subject describes never doubting that either parent would show up when needed."
    ),
    temperament_self_description=(
        "Subject describes being an even-keeled, curious child who got along easily with peers and "
        "adults alike, with no notable behavioral concerns reported at any point in school. Subject "
        "describes a mild tendency toward perfectionism in schoolwork but nothing that caused distress."
    ),
    experiences=[
        _exp("lo_e01", 6, 1, "Subject starts elementary school and settles in within the first week, quickly making friends."),
        _exp("lo_e02", 9, 1, "Subject's grandfather dies after a long illness; the family grieves together and Subject describes the funeral as sad but not frightening."),
        _exp("lo_e03", 12, 1, "Subject joins a youth soccer league and plays for several years, describing it as a source of steady friendships."),
        _exp("lo_e04", 15, 1, "Subject has a minor falling-out with a close friend over a misunderstanding; they reconcile within a few weeks."),
        _exp("lo_e05", 18, 1, "Subject leaves for a nearby state college, rooming with a friend from high school, and describes the transition as smooth."),
        _exp("lo_e06", 22, 1, "Subject graduates and takes a job in the same state, staying close to family; describes feeling no urgency to move far away."),
        _exp("lo_e07", 26, 1, "Subject enters a stable long-term relationship with a coworker; both families get along well from early on."),
    ],
)


ALL_FIXTURES = {
    "brandon": BRANDON,
    "complex": COMPLEX,
    "mixed": MIXED,
    "low_adversity": LOW_ADVERSITY,
}
