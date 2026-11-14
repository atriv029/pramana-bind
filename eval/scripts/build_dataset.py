"""Build the development and held-out item files.

Labels were written by reading each source passage, BEFORE any system was run
on the held-out items, and never from a system's output. Drafting provenance
is recorded per item. Reviewer status starts as 'pending' for every item.

Label = whether the SUPPLIED PASSAGE supports the claim (S) or not (N).
For statutory items this is support by the excerpt only; it is not a statement
about current law. For AVeriTeC-derived items the passage is one evidence
answer from AVeriTeC; the AVeriTeC claim-level verdict is kept as metadata and
is NOT the label.
"""
import hashlib
import json
import sys
from pathlib import Path

from pravrudhi.application.nyaya import load_corpus

AV = json.load(open(sys.argv[1]))  # AVeriTeC data/dev.json
OUT = Path(sys.argv[2])
corpus = load_corpus().by_id

S, N = "supported", "not_supported"
# (claim, label, subtype, evidence substring, rationale)
STAT = {
 "BSA/Section 53": [
  ("Under section 53 of the Bharatiya Sakshya Adhiniyam, a fact that the parties agree to admit at the hearing does not need to be proved.", S, None, "No fact needs to be proved in any proceeding which the parties thereto or their agents agree to admit at the hearing", "Restates the opening clause."),
  ("Section 53 of the Bharatiya Sakshya Adhiniyam means a court can never require proof of a fact the parties have admitted.", N, "contradicted", "Provided that the Court may, in its discretion, require the facts admitted to be proved otherwise than by such admissions", "The proviso lets the Court require proof."),
  ("Section 53 of the Bharatiya Sakshya Adhiniyam provides that facts admitted to the police during investigation need not be proved.", N, "missing_evidence", "agree to admit at the hearing, or which, before the hearing, they agree to admit by any writing under their hands", "The section covers admissions at the hearing, in writing before it, or by pleadings; nothing about the police."),
  ("Section 53 of the Bharatiya Sakshya Adhiniyam lets the court, in its discretion, require an admitted fact to be proved by other means.", S, None, "Provided that the Court may, in its discretion, require the facts admitted to be proved otherwise than by such admissions", "Restates the proviso."),
 ],
 "COI/Article 96": [
  ("While a resolution for the Speaker's removal is under consideration, the Speaker shall not preside over the House of the People even if he is present.", S, None, "the Speaker, or while any resolution for the removal of the Deputy Speaker from his office is under consideration, the Deputy Speaker, shall not, though he is present, preside", "Clause (1)."),
  ("During proceedings on a resolution for his removal, the Speaker has a casting vote if the votes are equal.", N, "contradicted", "but not in the case of an equality of votes", "Clause (2) excludes a vote on an equality of votes."),
  ("Article 96 bars the Speaker from speaking or taking part in the proceedings while a resolution for his removal is under consideration.", N, "contradicted", "The Speaker shall have the right to speak in, and otherwise to take part in the proceedings of", "Clause (2) gives the right to speak and take part."),
  ("The Speaker may vote in the first instance on a resolution for his own removal.", S, None, "be entitled to vote only in the first instance on such resolution", "Clause (2)."),
  ("Article 96 gives the Deputy Speaker the right to speak and to vote in the first instance while a resolution for the Deputy Speaker's removal is being considered.", N, "misbinding", "The Speaker shall have the right to speak in", "Clause (2) names only the Speaker; the excerpt says nothing of the Deputy Speaker's right to speak or vote."),
 ],
 "COI/Article 23": [
  ("Article 23 prohibits traffic in human beings and begar.", S, None, "Traffic in human beings and begar and other similar forms of forced labour are prohibited", "Clause (1)."),
  ("Article 23 prohibits the State from imposing any form of compulsory service.", N, "exception_omitted", "Nothing in this article shall prevent the State from imposing compulsory service for public purposes", "Clause (2) preserves compulsory service for public purposes."),
  ("Under Article 23 the State may impose compulsory service for public purposes, but may not discriminate in doing so on grounds only of religion, race, caste or class.", S, None, "in imposing such service the State shall not make any discrimination on grounds only of religion, race, caste or class or any of them", "Clause (2)."),
  ("Article 23 prescribes imprisonment of up to seven years for trafficking in human beings.", N, "missing_evidence", "shall be an offence punishable in accordance with law", "No punishment is specified in the article."),
 ],
 "COI/Article 133": [
  ("Under Article 133, an appeal lies to the Supreme Court from any judgment in a civil proceeding of a High Court.", N, "exception_omitted", "if the High Court certifies under article 134A", "Omits the certification condition."),
  ("Under Article 133, a civil appeal lies to the Supreme Court if the High Court certifies that the case involves a substantial question of law of general importance which, in its opinion, needs to be decided by the Supreme Court.", S, None, "that the case involves a substantial question of law of general importance", "Clause (1)(a) and (b)."),
  ("Article 133 allows an appeal to the Supreme Court as of right from the judgment of a single Judge of a High Court.", N, "contradicted", "no appeal shall, unless Parliament by law otherwise provides, lie to the Supreme Court from the judgment, decree or final order of one Judge of a High Court", "Clause (3) bars it unless Parliament provides otherwise."),
  ("Unless Parliament by law provides otherwise, no appeal lies to the Supreme Court under Article 133 from the judgment of one Judge of a High Court.", S, None, "no appeal shall, unless Parliament by law otherwise provides, lie to the Supreme Court from the judgment, decree or final order of one Judge of a High Court", "Clause (3)."),
 ],
 "COI/Article 30": [
  ("All minorities, whether based on religion or language, have the right to establish and administer educational institutions of their choice.", S, None, "All minorities, whether based on religion or language, shall have the right to establish and administer educational institutions of their choice", "Clause (1)."),
  ("Article 30 gives every citizen the right to establish and administer educational institutions.", N, "scope_inflation", "All minorities, whether based on religion or language", "The right is given to minorities, not to every citizen."),
  ("Article 30 protects only religious minorities.", N, "contradicted", "whether based on religion or language", "Linguistic minorities are expressly included."),
  ("Article 30 requires the State to give financial aid to every minority educational institution.", N, "scope_inflation", "The State shall not, in granting aid to educational institutions, discriminate", "Only non-discrimination in granting aid is required; no duty to aid."),
  ("In granting aid to educational institutions, the State may not discriminate against an institution on the ground that it is managed by a minority.", S, None, "discriminate against any educational", "Clause (2)."),
 ],
 "BSA/Section 128": [
  ("A married person cannot be compelled to disclose a communication made to him during marriage by his spouse.", S, None, "shall be compelled to disclose any communication made to him during marriage", "Opening clause."),
  ("Communications between spouses during marriage can never be disclosed in any proceeding.", N, "exception_omitted", "except in suits between married persons", "Consent and two classes of proceedings are excepted."),
  ("The bar on disclosing marital communications does not apply in suits between married persons.", S, None, "except in suits between married persons", "Stated exception."),
  ("The protection for marital communications ends once the marriage has ended.", N, "contradicted", "No person who is or has been married", "The text covers a person who 'has been married'."),
 ],
 "COI/Article 203": [
  ("Estimates of expenditure charged upon the Consolidated Fund of a State are not submitted to the vote of the Legislative Assembly.", S, None, "shall not be submitted to the vote of the Legislative Assembly", "Clause (1)."),
  ("Estimates of expenditure charged upon the Consolidated Fund of a State cannot be discussed in the Legislature.", N, "contradicted", "nothing in this clause shall be construed as preventing the discussion in the Legislature of any of those estimates", "Discussion is expressly preserved."),
  ("The Legislative Assembly may assent to a demand for a grant subject to a reduction of the amount specified in it.", S, None, "to assent to any demand subject to a reduction of the amount specified therein", "Clause (2)."),
  ("The Legislative Assembly may increase the amount of a demand for a grant.", N, "missing_evidence", "to assent, or to refuse to assent, to any demand, or to assent to any demand subject to a reduction", "Only assent, refusal and reduction are provided."),
  ("No demand for a grant may be made except on the recommendation of the Speaker.", N, "misbinding", "except on the recommendation of the Governor", "The recommendation is the Governor's."),
 ],
 "COI/Article 179": [
  ("A Speaker of an Assembly must vacate his office if he ceases to be a member of the Assembly.", S, None, "shall vacate his office if he ceases to be a member of the Assembly", "Clause (a)."),
  ("The Speaker of an Assembly may be removed by a resolution passed by a majority of the members present and voting.", N, "contradicted", "passed by a majority of all the then members of the Assembly", "The majority required is of all the then members."),
  ("A resolution to remove the Speaker of an Assembly may be moved at any time without notice.", N, "contradicted", "unless at least fourteen days", "Fourteen days' notice is required."),
  ("When the Assembly is dissolved, the Speaker vacates his office immediately.", N, "temporal", "the Speaker shall not vacate his office until immediately before the first meeting of the Assembly after the dissolution", "The second proviso keeps him in office until just before the next Assembly's first meeting."),
  ("At least fourteen days' notice must be given before a resolution to remove the Speaker of an Assembly is moved.", S, None, "notice has been given of the intention to move the resolution", "First proviso."),
 ],
 "BNSS/Section 81": [
  ("A police officer who is to execute a warrant beyond the local jurisdiction of the issuing Court shall ordinarily take it for endorsement to an Executive Magistrate or to a police officer not below the rank of an officer in charge of a police station.", S, None, "he shall ordinarily take it for endorsement either to an Executive Magistrate or to a police officer not below the rank of an officer in charge of a police station", "Sub-section (1)."),
  ("A warrant can never be executed outside the issuing Court's local jurisdiction without an endorsement.", N, "exception_omitted", "may execute the same without such endorsement", "Sub-section (3) allows execution without endorsement where delay would prevent it."),
  ("If the delay in obtaining the endorsement would prevent execution, the police officer may execute the warrant without it.", S, None, "may execute the same without such endorsement", "Sub-section (3)."),
  ("Section 81 of the BNSS requires the endorsement to be obtained within twenty-four hours.", N, "missing_evidence", "shall endorse his name thereon", "No time limit appears in the section."),
 ],
 "BNS/Section 220": [
  ("Bidding at a sale held by the lawful authority of a public servant without intending to perform the obligations of the bid is punishable with imprisonment of up to one month, or a fine of up to two hundred rupees, or both.", S, None, "bids for such property not intending to perform the obligations under which he lays himself by such bidding", "Second limb and the punishment clause."),
  ("Section 220 of the BNS prescribes imprisonment of up to one year.", N, "contradicted", "for a term which may extend to one month", "The maximum is one month."),
  ("Section 220 of the BNS punishes anyone who bids at a sale held by authority of a public servant.", N, "scope_inflation", "whom he knows to be under a legal incapacity to purchase that property at that sale", "Only bidding for a person known to be incapacitated, or without intent to perform, is punished."),
  ("Under section 220 of the BNS the offender must be both imprisoned and fined.", N, "contradicted", "or with both", "Imprisonment, fine, or both."),
 ],
 "BSA/Section 48": [
  ("In a prosecution under section 64 of the Bharatiya Nyaya Sanhita where consent is in issue, evidence of the victim's previous sexual experience is not relevant on the issue of consent.", S, None, "previous sexual experience with any person shall not be relevant on the issue of such consent", "Within the listed offences and the consent condition."),
  ("Under section 48 of the Bharatiya Sakshya Adhiniyam, evidence of the victim's character is irrelevant in every criminal prosecution.", N, "scope_inflation", "In a prosecution for an offence under section 64", "Limited to listed offences where consent is in issue."),
  ("Section 48 of the Bharatiya Sakshya Adhiniyam makes evidence of the accused's character irrelevant.", N, "misbinding", "evidence of the character of the victim", "The section concerns the victim, not the accused."),
  ("Section 48 of the Bharatiya Sakshya Adhiniyam also applies to prosecutions for attempts to commit the listed offences.", S, None, "or for attempt to commit any such offence", "Stated."),
 ],
 "BNSS/Section 314": [
  ("When the accused is present in Court in person and evidence is given in a language he does not understand, it must be interpreted to him in open Court in a language he understands.", S, None, "it shall be interpreted to him in open Court in a language understood by him", "Sub-section (1)."),
  ("All evidence must be interpreted to the accused in a language he understands, whether or not he is present in Court.", N, "scope_inflation", "and he is present in Court in person", "The duty in sub-section (1) is conditioned on his presence in person."),
  ("The Court must interpret in full every document put in for the purpose of formal proof.", N, "contradicted", "it shall be in the discretion of the Court to interpret as much thereof as appears necessary", "Left to the Court's discretion."),
  ("How much of a document put in for formal proof is interpreted is in the discretion of the Court.", S, None, "it shall be in the discretion of the Court to interpret as much thereof as appears necessary", "Sub-section (3)."),
 ],
 "COI/Article 156": [
  ("The Governor holds office during the pleasure of the President.", S, None, "The Governor shall hold office during the pleasure of the President", "Clause (1)."),
  ("A Governor has a guaranteed, fixed term of five years.", N, "exception_omitted", "Subject to the foregoing provisions of this article", "The five-year term is subject to the President's pleasure and to resignation."),
  ("A Governor must leave office on the day his five-year term expires.", N, "contradicted", "continue to hold office until his successor enters upon his office", "The proviso continues him until a successor enters."),
  ("A Governor may resign his office by writing under his hand addressed to the President.", S, None, "resign his office", "Clause (2)."),
  ("A Governor may be removed only through impeachment by Parliament.", N, "missing_evidence", "during the pleasure of the President", "Impeachment is not mentioned; tenure is at the President's pleasure."),
 ],
 "BNSS/Section 39": [
  ("A person who commits a non-cognizable offence in the presence of a police officer and refuses on demand to give his name and residence may be arrested by that officer so that his name or residence may be ascertained.", S, None, "he may be arrested by such officer in order that his name or residence may be ascertained", "Sub-section (1)."),
  ("Under section 39 of the BNSS a police officer may arrest any person who refuses to give his name and residence.", N, "scope_inflation", "has committed or has been accused of committing a non-cognizable offence", "Limited to persons who committed or are accused of a non-cognizable offence in the officer's presence."),
  ("A person arrested under section 39 of the BNSS may be kept by the police for up to seven days while his identity is ascertained.", N, "contradicted", "within twenty-four hours from the time of arrest", "After twenty-four hours he must be forwarded to a Magistrate."),
  ("If a person arrested under section 39 of the BNSS is not resident in India, the bail bond must be secured by a surety or sureties resident in India.", S, None, "the bail bond shall be secured by a surety or sureties resident in India", "Proviso."),
  ("Once the true name and residence of a person arrested under section 39 of the BNSS are ascertained, he must be kept in custody until he is produced before a Magistrate.", N, "contradicted", "he shall be released on a bond or bail bond", "He is to be released on bond."),
 ],
 "BNSS/Section 16": [
  ("Subject to the control of the State Government, the District Magistrate may define the local limits of the areas within which Executive Magistrates may exercise their powers.", S, None, "the District Magistrate may, from time to time, define the local limits of the areas", "Sub-section (1)."),
  ("The State Government defines the local limits of the Executive Magistrates' areas, subject to the control of the District Magistrate.", N, "misbinding", "Subject to the control of the State Government, the District Magistrate may", "Roles are reversed."),
  ("The jurisdiction of every Executive Magistrate always extends throughout the district.", N, "exception_omitted", "Except as otherwise provided by such definition", "Subject to the District Magistrate's definition of local limits."),
 ],
 "COI/Article 193": [
  ("A person who sits or votes in a State Legislature when he knows he is disqualified is liable to a penalty of five hundred rupees for each day on which he does so.", S, None, "he shall be liable in respect of each day on which he so sits or votes to a penalty of five hundred rupees", "Stated."),
  ("The penalty under Article 193 is a single sum of five hundred rupees, however many days the person sits.", N, "contradicted", "in respect of each day on which he so sits or votes", "The penalty is per day."),
  ("Article 193 makes sitting in a State Legislature while disqualified a criminal offence punishable with imprisonment.", N, "missing_evidence", "to be recovered as a debt due to the State", "Only a money penalty recoverable as a debt."),
  ("Any disqualified person who sits in a State Legislature is liable to the penalty under Article 193 whether or not he knows of the disqualification.", N, "exception_omitted", "when he knows that he is not qualified or that he is disqualified", "Knowledge is a stated condition for the disqualification limb."),
 ],
 "COI/Article 212": [
  ("The validity of proceedings in the Legislature of a State cannot be called in question on the ground of an alleged irregularity of procedure.", S, None, "shall not be called in question on the ground of any alleged irregularity of procedure", "Clause (1)."),
  ("Article 212 bars courts from questioning the validity of State Legislature proceedings on any ground whatsoever.", N, "scope_inflation", "on the ground of any alleged irregularity of procedure", "Only the ground of procedural irregularity is barred."),
  ("Under Article 212, no member of a State Legislature is subject to the jurisdiction of any court for anything he does.", N, "scope_inflation", "in respect of the exercise by him of those powers", "Limited to officers/members vested with procedural powers, and to the exercise of those powers."),
 ],
}
STAT_DEV = {
 "BNS/Section 205": [
  ("Wearing a garb resembling one used by a class of public servants, with the intention that it be believed that one belongs to that class, is punishable with imprisonment of up to three months, or a fine of up to five thousand rupees, or both.", S, None, "shall be punished with imprisonment of either description for a term which may extend to three months", "Restates the section."),
  ("Section 205 of the BNS punishes anyone who wears a garb resembling a public servant's uniform.", N, "scope_inflation", "with the intention that it may be believed, or with the knowledge that it is likely to be believed", "Intention or knowledge is required, and the wearer must not belong to that class."),
  ("Section 205 of the BNS prescribes imprisonment of up to three years.", N, "contradicted", "for a term which may extend to three months", "Three months."),
 ],
 "COI/Article 318": [
  ("The conditions of service of a member of a Public Service Commission may not be varied to his disadvantage after his appointment.", S, None, "shall not be varied to his disadvantage after his appointment", "Proviso."),
  ("In the case of a State Public Service Commission, the President determines the number of members of the Commission.", N, "misbinding", "in the case of a State Commission, the Governor", "The Governor does, for a State Commission."),
  ("The conditions of service of a Public Service Commission member cannot be changed in any way after his appointment.", N, "scope_inflation", "shall not be varied to his disadvantage", "Only disadvantageous variation is barred."),
 ],
 "BNSS/Section 466": [
  ("A sentence of death passed on an escaped convict takes effect immediately, subject to the earlier provisions.", S, None, "such sentence shall, subject to the provisions hereinbefore contained, take effect immediately", "Sub-section (1)."),
  ("Any new sentence of imprisonment for a term passed on an escaped convict takes effect immediately.", N, "exception_omitted", "if such sentence is not severer in kind", "Only if severer in kind; otherwise after the unexpired remainder."),
  ("For this purpose, rigorous imprisonment is deemed severer in kind than simple imprisonment.", S, None, "a sentence of rigorous imprisonment shall be deemed to be severer in kind than a sentence of simple imprisonment", "Sub-section (3)."),
 ],
 "COI/Article 235": [
  ("Control over district courts and the courts subordinate to them is vested in the High Court.", S, None, "shall be vested in the High Court", "Stated."),
  ("Article 235 takes away a judicial officer's right of appeal under the law regulating his conditions of service.", N, "contradicted", "nothing in this article shall be construed as taking away from any such person any right of appeal", "Expressly preserved."),
  ("Article 235 vests in the High Court the posting and promotion of district judges.", N, "scope_inflation", "holding any post inferior to the post of district judge", "Posting and promotion are mentioned for posts inferior to district judge."),
 ],
 "BNS/Section 105": [
  ("Culpable homicide not amounting to murder, where the act is done with the intention of causing death, is punishable with imprisonment for life, or imprisonment of not less than five years which may extend to ten years, and fine.", S, None, "for a term which shall not be less than five years but which may extend to ten years", "First limb."),
  ("Where the act is done with knowledge that it is likely to cause death but without intention, section 105 of the BNS sets a minimum term of five years.", N, "misbinding", "with imprisonment of either description for a term which may extend to ten years and with fine, if the act is done with the knowledge", "The five-year minimum belongs to the intention limb only."),
  ("Section 105 of the BNS prescribes the death penalty.", N, "contradicted", "shall be punished with imprisonment for life", "No death penalty in the section."),
 ],
}
# AVeriTeC-derived: (claim index, question index, answer index) -> items; origin 'averitec' = claim text is AVeriTeC's
AVT = {
 (371, 1, 0): [
  ("averitec", N, "missing_evidence", "in the case of Government servants of the following categories", "The passage gives the general limit and a relaxation for certain Government servants; it says nothing about Muslim candidates."),
  ("The upper age limit of 30 years for the examination is relaxable up to 35 years for certain categories of Government servants.", S, None, "The upper age‐limit of 30 years will be relaxable upto 35 years in the case of Government servants of the following categories", "Stated in (b)."),
  ("The upper age limit for the examination is relaxable up to 35 years for all Government servants.", N, "scope_inflation", "Government servants of the following categories", "Only listed categories, under listed authorities."),
 ],
 (158, 4, 0): [
  ("averitec", N, "missing_evidence", "The effectiveness of the antibody therapy was tested by employing a fetal tissue cell line", "The passage says the therapy was tested with a fetal cell line; it does not say Trump was given it, nor that it was developed from fetal tissue."),
  ("According to Regeneron, the effectiveness of its antibody therapy was tested using a fetal tissue cell line dating from the 1980s.", S, None, "tested by employing a fetal tissue cell line from the 1980s", "Stated."),
 ],
 (48, 0, 0): [
  ("averitec", N, "contradicted", "which makes a case recovery rate of 67.97%", "Reported recovery rates are 39.88% (US) and 67.97% (global)."),
  ("As of October 23, the reported global case fatality rate was about 2.7%.", S, None, "which makes for a 2.72% case fatality rate", "Stated."),
  ("As of October 23, the case recovery rate in the United States was about 68%.", N, "misbinding", "This makes for a case recovery rate of 39.88%", "68% is the global figure; the US figure is 39.88%."),
 ],
 (222, 1, 0): [
  ("averitec", N, "misbinding", "Nigeria – 200 million", "The 200 million is the projected ADDITION to Nigeria's urban population over four decades, not its population."),
  ("India is expected to add about 497 million people to its urban population over the next four decades.", S, None, "India will add another 497 million to its urban population", "Stated."),
 ],
 (245, 0, 0): [
  ("averitec", N, "contradicted", "This is misleading", "The passage calls it misleading to cite isolated mis-sent ballots as evidence of fraud."),
  ("Election officials say that steps including signature verification prevent imposters from returning ballots in place of another voter.", S, None, "election officials say steps including signature verification prevent imposters from returning ballots in place of another voter", "Stated."),
 ],
 (30, 0, 0): [
  ("averitec", N, "contradicted", "100% Fake News", "Pogba calls the reports fake."),
  ("Pogba said he was taking legal action against the publishers and spreaders of the story.", S, None, "I am taking legal action against the publishers and spreaders", "Stated."),
 ],
 (60, 5, 0): [
  ("averitec", N, "contradicted", "This means that an employee earns 77% of their normal wage", "The passage gives 77%, for a scheme requiring 33% of hours worked; nothing on tier 3 closures or Universal Credit."),
  ("To be eligible under the scheme, an employee must work at least 33% of their usual hours.", S, None, "the employee must work at least 33% of their usual hours", "Stated."),
  ("Under the scheme an employee always earns 77% of their normal wage.", N, "exception_omitted", "where the Government contribution has not been capped", "Only where the contribution is not capped."),
 ],
 (116, 0, 0): [
  ("averitec", N, "contradicted", "The video is deceptively edited and misleading", "The passage says the quote is cut mid-sentence and gives the full remark."),
  ("The fact-check rated the Facebook post Mostly False.", S, None, "We rate this Facebook post Mostly False", "Stated."),
 ],
 (451, 3, 0): [
  ("averitec", N, "contradicted", "This REMAINS ILLEGAL under SB 145", "The passage says the conduct remains illegal."),
  ("Under SB 145, where the couple is close in age and the behavior was voluntary, a judge can decide whether the older party should be on the sex offender registry.", S, None, "whether or not the older party should be on the sex offender registry", "Stated."),
  ("SB 145 lets judges decide on sex offender registration in every case of sex with a minor.", N, "scope_inflation", "if the couple is close in age and the behavior was voluntary", "Limited by age gap, voluntariness and the kinds of contact listed."),
 ],
 (402, 0, 0): [
  ("averitec", S, None, "Section 21 of the Act prescribes a fine of N50,000 or six months imprisonment or both", "An offence under the CBN Act, with imprisonment among the penalties."),
  ("People are regularly arrested and prosecuted in Nigeria for spraying Naira notes.", N, "contradicted", "there is no evidence anyone has been arrested and prosecuted for the offence", "The passage says there is no evidence of any arrest or prosecution."),
 ],
 (231, 1, 0): [
  ("A report estimates Nigeria's urban population in 1960 at about 7 million.", S, None, "The report estimates Nigeria’s 1960 urban population at 6.96 million", "Stated."),
  ("Most countries define 'urban' purely by population size.", N, "contradicted", "use an administrative definition", "Nearly two thirds use an administrative definition, usually with added elements."),
 ],
 (377, 0, 0): [
  ("averitec", N, "contradicted", "they have specifically said the claim of an Antifa forest fire campaign is 100% false", "Authorities call the claim false."),
  ("Authorities reported at least two arrests for arson.", S, None, "authorities have reported at least two arrests for arson", "Stated."),
  ("Authorities said no one had been arrested for arson in connection with the fires.", N, "contradicted", "at least two arrests for arson", "Two arrests were reported."),
 ],
 (338, 1, 0): [
  ("averitec", N, "missing_evidence", "we need to study the effects of generations of discrimination", "The passage quotes Harris on studying effects; no tax on homes is mentioned."),
  ("In a March 2019 interview, Harris said the term reparations means different things to different people.", S, None, "the term reparations, it means different things to different people", "Stated."),
 ],
 (285, 1, 0): [
  ("averitec", N, "misbinding", "to allow judges to have a say on whether to list someone as a sex offender", "The law concerns registry discretion, not sentence length."),
  ("Newsom signed legislation that lets judges use discretion over sex offender registration in cases involving voluntary oral or anal sex with a minor.", S, None, "permits judges to use the same discretion when the case involves voluntary oral or anal sex", "Stated."),
 ],
 (360, 6, 0): [
  ("averitec", N, "contradicted", "only ‘appropriate practitioners’ administer vaccines", "The passage says only appropriate practitioners may currently administer vaccines."),
  ("The regulations currently require that only 'appropriate practitioners' administer vaccines.", S, None, "the HMRs require that only ‘appropriate practitioners’ administer vaccines", "Stated."),
 ],
 (316, 0, 0): [
  ("averitec", N, "missing_evidence", "have agreed to temporarily restrict all non-essential travel", "The passage reports the restriction; it says nothing about Canada wanting to reopen."),
  ("Canada and the United States agreed to temporarily restrict non-essential travel across their border, taking effect on March 21, 2020.", S, None, "The new measures will take effect at 12:01 a.m. EDT on Saturday, March 21, 2020", "Stated."),
  ("Canada and the United States agreed to restrict non-essential travel across the border indefinitely.", N, "temporal", "end at 12:00 p.m. EDT on Tuesday, April 21, 2020", "The measures are temporary with a stated end date and review."),
 ],
 (437, 2, 0): [
  ("averitec", N, "contradicted", "between a teenager age 15 and over and a partner within 10 years of age", "The passage is about teenagers 15 and over with a partner within 10 years; an 11-year-old is outside it."),
  ("For oral and anal intercourse, sex offender registration was mandated in all situations, with no judicial discretion.", S, None, "sex offender registration is mandated under all situations, with no judicial discretion", "Stated."),
 ],
 (496, 3, 0): [
  ("Biden's plan specifies free lawyers for migrants.", N, "contradicted", "But it doesn’t specify \"free lawyers.\"", "The passage says the plan does not specify free lawyers."),
  ("Biden would double the number of immigration judges.", S, None, "Biden would double the number of immigration judges", "Stated."),
 ],
 (414, 3, 0): [
  ("averitec", N, "missing_evidence", "Uyghurs live for the most part in northwestern China", "The passage is about where Uyghurs live; it has no birthrate figures."),
  ("Uyghurs live for the most part in the Xinjiang Uyghur Autonomous Region of northwestern China.", S, None, "Uyghurs live for the most part in northwestern China, in the Xinjiang Uyghur Autonomous Region", "Stated."),
  ("All Uyghurs live in China's Xinjiang region.", N, "scope_inflation", "a small number live in the Central Asian republics", "'For the most part'; some live in Central Asia."),
 ],
}
AVT_DEV = {
 (386, 0, 1): [
  ("averitec", N, "missing_evidence", "it was classified as a pandemic", "The passage explains the terms; it says nothing about the CDC changing its website."),
  ("Because the disease spread across several countries and affected a large number of people, it was classified as a pandemic.", S, None, "it was classified as a pandemic", "Stated."),
 ],
 (265, 2, 0): [
  ("averitec", N, "missing_evidence", "Voter fraud is a serious federal and state crime", "The passage describes penalties; it does not speak to the application sent in New Mexico."),
  ("In a federal election, each act of voter fraud can be punished by five years in prison and a US$10,000 fine.", S, None, "each act of voter fraud can be punished by five years in prison and a US$10,000 fine", "Stated."),
 ],
 (441, 1, 0): [
  ("averitec", N, "contradicted", "It is most likely that the idol of Goddess Kali caught fire by accident", "The temple secretary says it was most likely an accident."),
  ("The temple committee secretary said the committee had not filed an FIR.", S, None, "We have not filed any FIR since we do not suspect foul play", "Stated."),
 ],
}


def sha(t):
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def stat_items(table, split):
    out = []
    for doc_id, items in table.items():
        doc = corpus[doc_id]
        fam = "stat:" + doc_id
        for i, (claim, label, sub, ev, why) in enumerate(items):
            assert ev in doc.text, (doc_id, ev)
            s = doc.text.index(ev)
            out.append({
                "id": f"{split}-stat-{doc_id.replace('/', '-').replace(' ', '')}-{i}", "family": fam, "slice": "statutory",
                "split": split, "claim": claim, "citation": f"{doc.act}, {doc.section}",
                "source_text": doc.text, "source_sha256": sha(doc.text),
                "source_locator": f"pravrudhi statute corpus: {doc_id} ({doc.title})",
                "retrieval": "selected by the item author from the shipped corpus; no retrieval system",
                "label": label, "subtype": sub, "evidence_spans": [[s, s + len(ev)]], "rationale": why,
                "task_note": "support by the supplied excerpt only; not a determination of current law",
                "drafting": "claim, label and rationale drafted by an AI assistant (Claude, in the sprint session) from the excerpt",
                "review": {"status": "pending", "reviewer_1": None, "reviewer_2": None, "adjudication": None},
            })
    return out


def avt_items(table, split):
    out = []
    for (ci, qi, ai), items in table.items():
        x = AV[ci]
        a = x["questions"][qi]["answers"][ai]
        text = a["answer"]
        for i, (claim, label, sub, ev, why) in enumerate(items):
            assert ev in text, (ci, ev)
            s = text.index(ev)
            orig = claim == "averitec"
            out.append({
                "id": f"{split}-avt-{ci}-{i}", "family": f"avt:{ci}", "slice": "averitec_derived", "split": split,
                "claim": x["claim"] if orig else claim, "citation": a.get("source_url", ""),
                "source_text": text, "source_sha256": sha(text),
                "source_locator": f"AVeriTeC dev.json claim #{ci}, question {qi}, answer {ai} (extractive); {a.get('source_url', '')}",
                "retrieval": "evidence answer selected by AVeriTeC annotators; passage chosen by the item author",
                "label": label, "subtype": sub, "evidence_spans": [[s, s + len(ev)]], "rationale": why,
                "task_note": "passage-level support. The AVeriTeC claim-level verdict is metadata, not the label.",
                "averitec": {"claim_index": ci, "claim_level_label": x["label"], "claim_is_original": orig},
                "drafting": ("AVeriTeC claim; " if orig else "claim drafted by an AI assistant (Claude); ")
                            + "passage-level label and rationale drafted by an AI assistant (Claude)",
                "review": {"status": "pending", "reviewer_1": None, "reviewer_2": None, "adjudication": None},
            })
    return out


dev = stat_items(STAT_DEV, "dev") + avt_items(AVT_DEV, "dev")
test = stat_items(STAT, "test") + avt_items(AVT, "test")
assert not {i["family"] for i in dev} & {i["family"] for i in test}
assert len({i["id"] for i in dev + test}) == len(dev + test)
for name, items in (("dev", dev), ("test", test)):
    p = OUT / f"{name}.jsonl"
    p.write_text("".join(json.dumps(i, ensure_ascii=False, sort_keys=True) + "\n" for i in items), encoding="utf-8")
    n = len(items); k = sum(i["label"] == S for i in items)
    print(name, n, "items;", k, "supported;", n - k, "not_supported;", len({i["family"] for i in items}), "families;",
          "sha256", hashlib.sha256(p.read_bytes()).hexdigest())
