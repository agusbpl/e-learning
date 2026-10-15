import json
import unittest

from tutor_output import INCOMPLETE_REPLY, unpack_reply


class TutorOutputTests(unittest.TestCase):
    def test_recovers_final_json_after_commentary_without_exposing_prefix(self):
        answer={'reply':'Compará el stock con los pedidos.','status':'pending','evidence':[]}
        for prefix in ['El estudiante envió una respuesta. Ahora debo producir el JSON.\n',
                       '<think>PRIVATE <data>not final</data></think>\n```json\n']:
            with self.subTest(prefix=prefix):
                reply,parsed,damaged=unpack_reply(prefix+json.dumps(answer),structured=True)
                self.assertEqual(reply,answer['reply'])
                self.assertEqual(parsed,answer)
                self.assertFalse(damaged)

    def test_unfinished_analysis_is_never_student_facing(self):
        for raw in ['<think>PRIVATE', '<analysis>PRIVATE', 'El estudiante envió una respuesta. Analicemos contra la rúbrica.', 'We need to evaluate each criterion.', 'Texto sin un campo de respuesta final']:
            with self.subTest(raw=raw):
                self.assertEqual(unpack_reply(raw,structured=True),(INCOMPLETE_REPLY,None,True))

    def test_complete_thinking_blocks_and_orphan_closers_are_removed_from_notes(self):
        for raw in ['<think>PRIVATE</think>Respuesta clara.', 'PRIVATE</think>Respuesta clara.', '<analysis>PRIVATE</analysis>Respuesta clara.']:
            self.assertEqual(unpack_reply(raw),('Respuesta clara.',None,False))
        self.assertEqual(unpack_reply('Texto normal del tutor.'),('Texto normal del tutor.',None,False))

    def test_truncated_final_reply_keeps_unicode_but_no_assessment(self):
        for raw in ['Analicemos primero.\n{"reply":"Explicaci\\u00f3n útil.", "status":', '{"status":"pending","reply":"Explicaci\\u00f3n útil.", "evidence":']:
            self.assertEqual(unpack_reply(raw,structured=True),('Explicación útil.',None,True))

    def test_private_text_inside_reply_cannot_be_rendered_or_assessed(self):
        raw=json.dumps({'reply':'<think>PRIVATE</think>Respuesta final.','status':'pending'})
        reply,parsed,damaged=unpack_reply(raw,structured=True)
        self.assertEqual(reply,'Respuesta final.')
        self.assertEqual(parsed['reply'],reply)
        self.assertFalse(damaged)
        self.assertEqual(unpack_reply('{"reply":"<think>PRIVATE"}',structured=True),(INCOMPLETE_REPLY,None,True))


if __name__=='__main__':
    unittest.main()
