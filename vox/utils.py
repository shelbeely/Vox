import glob
import os
from datetime import datetime, timedelta
from vox.fastapi_app import app

LLM_PERSONALITY_PROMPT_BASE = (
    "You are Vox, a supportive voice therapy coach built for trans individuals, created by Shelbeely, a trans woman developer. "
    "Your tone is warm, encouraging, and affirming, with a deep understanding of gender expression and voice training. "
    "Use the user's name and pronouns (provided below) in your responses to make them feel seen and supported. "
    "Use the subject pronoun(s) (e.g., 'she', 'pup') for subjects, the object pronoun(s) (e.g., 'her', 'pup') for objects, "
    "the possessive pronoun (e.g., 'hers', 'puppy') for possession, and the reflexive pronoun (e.g., 'herself', 'pupself') "
    "for reflexive actions (e.g., 'she hears herself', 'pup hears pupself'). "
    "For mixed pronouns (e.g., 'she/they'), alternate between the two subject pronouns (e.g., 'she’s great' then 'they’re amazing') "
    "and their corresponding object pronouns (e.g., 'her' then 'them') naturally across sentences for variety. "
    "If the user has 'any' pronouns, default to 'they/them/theirs/themselves' but mix in other pronouns creatively "
    "(e.g., 'xe', 'pup', 'zirself') for fun. "
    "Provide clear, practical feedback grounded in the data, and always aim to uplift the user in their journey to find their authentic voice.\n"
)

def cleanup_old_recordings():
    now = datetime.now()
    cutoff = now - timedelta(days=40)
    cutoff_timestamp = cutoff.timestamp()
    recordings_folder = 'recordings'
    for session_dir in glob.glob(os.path.join(recordings_folder, '*')):
        if os.path.isdir(session_dir):
            for file in glob.glob(os.path.join(session_dir, '*.wav')):
                if os.path.getmtime(file) < cutoff_timestamp:
                    try:
                        os.remove(file)
                        logger.info(f"Deleted old recording: {file}")
                    except Exception as e:
                        logger.error(f"Error deleting {file}: {e}")
            if not os.listdir(session_dir):
                os.rmdir(session_dir)
                logger.info(f"Deleted empty session directory: {session_dir}")

def log_activity(sid, action, details):
    logger.info(f"Session {sid} - {action}: {details}")


PRONOUN_EXAMPLES = {
    "she/her/hers/herself": "'She/her/hers/herself': 'She’s hitting great notes, I hear her clearly, hers is a strong voice, and she’s proud of herself.'",
    "he/him/his/himself": "'He/him/his/himself': 'He’s got a solid pitch, I hear him well, his tone is great, and he’s confident in himself.'",
    "they/them/theirs/themselves": "'They/them/theirs/themselves': 'They’re doing amazing, I hear them clearly, theirs is a unique voice, and they’re proud of themselves.'",
    "xe/xem/xirs/xemself": "'Xe/xem/xirs/xemself': 'Xe’s pitch is lovely, I hear xem clearly, xirs tone is unique, and xe’s proud of xemself.'",
    "ze/zir/zirs/zirself": "'Ze/zir/zirs/zirself': 'Ze’s resonance shines, encourage zir, zirs voice is strong, and ze sees zirself improving.'",
    "ze/hir/hirs/hirself": "'Ze’s voice is vibrant, I hear hir clearly, hirs tone is warm, and ze loves hirself.'",
    "ey/em/eirs/emself": "'Ey/em/eirs/emself': 'Ey’s pitch is steady, I hear em well, eirs voice is clear, and ey trusts emself.'",
    "ve/ver/vis/verself": "'Ve/ver/vis/verself': 'Ve’s tone is smooth, I hear ver easily, vis voice is distinct, and ve honors verself.'",
    "tey/ter/tem/terself": "'Tey/ter/tem/terself': 'Tey’s pitch is bright, I hear ter clearly, tem voice is lovely, and tey uplifts terself.'",
    "e/em/es/eself": "'E/em/es/eself': 'E’s resonance is strong, I hear em well, es tone is unique, and e supports eself.'",
    "zie/zim/zir/zirself": "'Zie/zim/zir/zirself': 'Zie’s voice glows, I hear zim clearly, zir tone is bold, and zie cherishes zirself.'",
    "sie/sir/hir/hirself": "'Sie/sir/hir/hirself': 'Sie’s pitch is rich, I hear sir well, hir voice is striking, and sie celebrates hirself.'",
    "it/it/its/itself": "'It/it/its/itself': 'It’s got a cool vibe, I hear it clearly, its tone is neat, and it’s happy with itself.'",
    "fae/faer/faers/faerself": "'Fae/faer/faers/faerself': 'Fae’s voice sparkles, I hear faer gently, faers tone is magical, and fae adores faerself.'",
    "ae/aer/aers/aerself": "'Ae/aer/aers/aerself': 'Ae’s pitch flows, I hear aer smoothly, aers voice is serene, and ae nurtures aerself.'",
    "per/per/pers/perself": "'Per/per/pers/perself': 'Per’s tone is steady, I hear per clearly, pers voice is calm, and per values perself.'",
    "pup/pup/puppy/pupself": "'Pup/pup/puppy/pupself': 'Pup’s pitch is adorable, I hear pup softly, puppy tone is sweet, and pup loves pupself.'",
    "kit/kit/kits/kitself": "'Kit/kit/kits/kitself': 'Kit’s voice is playful, I hear kit brightly, kits tone is fun, and kit enjoys kitself.'",
    "bun/bun/buns/bunself": "'Bun/bun/buns/bunself': 'Bun’s pitch is cozy, I hear bun warmly, buns tone is soft, and bun comforts bunself.'",
    "star/star/stars/starself": "'Star/star/stars/starself': 'Star’s voice shines, I hear star clearly, stars tone is radiant, and star celebrates starself.'",
    "void/void/voids/voidself": "'Void/void/voids/voidself': 'Void’s pitch is deep, I hear void softly, voids tone is vast, and void embraces voidself.'",
    "nyx/nyx/nyxs/nyxself": "'Nyx/nyx/nyxs/nyxself': 'Nyx’s voice is mysterious, I hear nyx gently, nyxs tone is dark, and nyx honors nyxself.'",
    "she/they/her/them/hers/theirs/herself/themselves": "'She/they/her/them/hers/theirs/herself/themselves': 'She’s doing great, I hear them clearly, hers is a lovely voice, and they’re proud of themselves.'",
    "he/they/him/them/his/theirs/himself/themselves": "'He/they/him/them/his/theirs/himself/themselves': 'He’s got a strong pitch, I hear them well, his tone is solid, and they trust themselves.'"
}
