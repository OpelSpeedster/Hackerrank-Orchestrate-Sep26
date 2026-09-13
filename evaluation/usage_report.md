# Model Usage and Evaluation Report

Run ID: `20260913T090121Z`
Generated at (UTC): `2026-09-13T09:01:21.819934+00:00`
Output: `/projects/challenge/output.csv`
Output SHA-256: `27d4b3350d22e4c518844b3df20df620442845f8f46b57813a724ad3ba6aa21a`

## Providers and models

- Provider: `Groq + Modal`
- Qwen extraction model: `qwen/qwen3.8-27b`
- Orchestrator model: `openai/gpt-oss-120b`
- Modal embedding/document model: `BAAI/bge-small-en-v1.5`
- Modal calls are enabled when `MODAL_ENDPOINT` is configured; deployment tokens remain environment-only.

## Requests and latency

- Requests processed: 250
- Valid requests: 250
- Fallback requests: 0
- Average latency (ms): 560.27
- P50 latency (ms): 373.98
- P95 latency (ms): 1486.40

## Model usage

- Total provider model calls: 270
- Groq model calls: 261
- Modal calls: 9
- Successful model calls: 19
- Orchestrator calls attempted: 250
- Qwen image extraction calls attempted: 11
- Failed provider calls: 251
- Timed-out Groq calls: 0
- Input tokens: 5726
- Output tokens: 2905
- Total tokens: 8631
- Average tokens per request: 34.52
- Estimated provider cost (USD): 0.00432230
- Estimated cost per request (USD): 0.00001729
- Model error categories: rate_limit=251

## Safety and orchestration metrics

- Guard calls attempted: 250
- Completed safety calls: 8
- Failed safety calls: 242
- Timed-out safety calls: 0
- Invalid safety responses: 0
- Flagged requests: 8
- Safety flag rate: 100.0000%

## Per-request execution

| request_id | latency_ms | valid | fallback | planned_steps | attempted_tools | successful_tools | model_calls | guard_status | qwen_status | guard_flagged | errors |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---:|---|
| request_100 | 677.08 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_101 | 2512.79 | True | False | 7 | 7 | 5 | 2 | failed | failed | False | guard_failed, qwen_failed |
| request_102 | 523.10 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_103 | 521.02 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_104 | 503.06 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_105 | 2482.20 | True | False | 7 | 7 | 5 | 2 | failed | failed | False | guard_failed, qwen_failed |
| request_106 | 170.49 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_107 | 188.08 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_108 | 173.12 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_109 | 150.65 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_110 | 153.03 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_111 | 166.50 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_112 | 169.49 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_113 | 2302.44 | True | False | 7 | 7 | 5 | 2 | failed | failed | False | guard_failed, qwen_failed |
| request_114 | 155.09 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_115 | 121.91 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_116 | 91.03 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_117 | 81.77 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_118 | 91.58 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_119 | 88.93 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_120 | 66.60 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_121 | 137.34 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_122 | 138.06 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_123 | 162.29 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_124 | 150.05 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_125 | 121.99 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_126 | 165.67 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_127 | 460.79 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_128 | 287.83 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_129 | 365.66 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_130 | 652.19 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_131 | 426.41 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_132 | 326.21 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_133 | 248.83 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_134 | 446.98 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_135 | 363.76 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_136 | 348.57 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_137 | 519.31 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_138 | 291.88 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_139 | 274.85 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_140 | 284.41 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_141 | 512.03 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_142 | 423.42 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_143 | 509.64 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_144 | 528.61 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_145 | 421.66 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_146 | 421.64 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_147 | 326.10 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_148 | 739.26 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_149 | 439.40 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_150 | 432.13 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_151 | 439.38 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_152 | 373.82 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_153 | 742.52 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_154 | 366.63 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_155 | 423.33 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_156 | 402.87 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_157 | 474.60 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_158 | 378.12 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_159 | 279.11 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_160 | 357.07 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_161 | 762.60 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_162 | 450.20 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_163 | 544.41 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_164 | 453.72 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_165 | 547.48 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_166 | 283.46 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_167 | 359.05 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_168 | 677.96 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_169 | 401.16 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_170 | 414.13 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_171 | 345.00 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_172 | 281.16 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_173 | 517.47 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_174 | 268.28 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_175 | 261.58 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_176 | 249.16 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_177 | 273.66 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_178 | 281.60 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_179 | 348.39 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_180 | 348.62 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_181 | 674.34 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_182 | 316.02 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_183 | 350.74 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_184 | 340.91 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_185 | 813.92 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_186 | 1222.07 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_187 | 477.78 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_188 | 878.75 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_189 | 405.71 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_190 | 410.63 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_191 | 380.72 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_192 | 464.50 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_193 | 799.35 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_194 | 465.36 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_195 | 415.55 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_196 | 438.53 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_197 | 244.56 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_198 | 232.51 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_199 | 254.90 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_200 | 422.16 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_201 | 336.95 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_202 | 310.92 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_203 | 292.79 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_204 | 381.54 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_205 | 354.63 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_206 | 344.56 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_207 | 328.73 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_208 | 302.34 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_209 | 334.12 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_210 | 460.79 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_211 | 404.46 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_212 | 455.13 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_213 | 315.14 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_214 | 475.48 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_215 | 418.78 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_216 | 572.67 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_217 | 761.74 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_218 | 375.85 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_219 | 381.18 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_220 | 308.23 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_221 | 274.45 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_222 | 311.93 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_223 | 404.11 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_224 | 402.76 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_225 | 433.04 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_226 | 804.28 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_227 | 440.79 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_228 | 444.26 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_229 | 421.43 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_230 | 389.92 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_231 | 388.89 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_232 | 406.67 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_233 | 409.46 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_234 | 392.10 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_235 | 391.92 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_236 | 373.98 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_237 | 400.58 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_238 | 273.33 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_239 | 273.05 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_240 | 273.28 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_241 | 248.42 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_242 | 492.14 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_243 | 469.47 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_244 | 458.73 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_245 | 447.01 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_246 | 309.65 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_247 | 337.56 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_248 | 327.04 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_249 | 625.49 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_250 | 348.97 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_251 | 320.94 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_252 | 353.34 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_253 | 456.11 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_254 | 477.52 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_255 | 411.16 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_256 | 436.64 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_257 | 1621.88 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_258 | 446.18 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_259 | 443.57 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_26 | 1073.43 | True | False | 7 | 6 | 6 | 1 | flagged | skipped | True |  |
| request_260 | 1401.09 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_261 | 473.11 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_262 | 406.30 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_263 | 732.70 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_264 | 573.21 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_265 | 390.52 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_266 | 320.32 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_267 | 242.35 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_268 | 258.29 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_269 | 588.71 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_27 | 1337.34 | True | False | 7 | 6 | 6 | 1 | flagged | skipped | True |  |
| request_270 | 588.77 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_271 | 1434.13 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_272 | 601.63 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_273 | 524.37 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_274 | 524.47 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_275 | 487.61 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_28 | 1451.58 | True | False | 7 | 6 | 6 | 1 | flagged | skipped | True |  |
| request_29 | 1260.61 | True | False | 7 | 6 | 6 | 1 | flagged | skipped | True |  |
| request_30 | 1054.29 | True | False | 7 | 6 | 6 | 1 | flagged | skipped | True |  |
| request_31 | 1486.40 | True | False | 7 | 6 | 6 | 1 | flagged | skipped | True |  |
| request_32 | 1412.35 | True | False | 7 | 6 | 6 | 1 | flagged | skipped | True |  |
| request_33 | 2616.20 | True | False | 7 | 7 | 6 | 2 | failed | completed | False | guard_failed |
| request_34 | 11176.33 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_35 | 1336.07 | True | False | 7 | 7 | 7 | 2 | flagged | completed | True |  |
| request_36 | 205.02 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_37 | 123.71 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_38 | 215.80 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_39 | 315.75 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_40 | 386.03 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_41 | 693.43 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_42 | 400.18 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_43 | 490.65 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_44 | 479.74 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_45 | 389.14 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_46 | 359.08 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_47 | 850.14 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_48 | 5924.35 | True | False | 7 | 7 | 5 | 2 | failed | failed | False | guard_failed, qwen_failed |
| request_49 | 280.88 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_50 | 158.37 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_51 | 287.66 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_52 | 163.22 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_53 | 251.27 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_54 | 162.74 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_55 | 5345.90 | True | False | 7 | 7 | 5 | 2 | failed | failed | False | guard_failed, qwen_failed |
| request_56 | 139.58 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_57 | 181.77 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_58 | 81.02 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_59 | 93.03 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_60 | 115.10 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_61 | 67.86 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_62 | 117.68 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_63 | 180.40 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_64 | 4751.46 | True | False | 7 | 7 | 5 | 2 | failed | failed | False | guard_failed, qwen_failed |
| request_65 | 102.67 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_66 | 68.73 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_67 | 409.90 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_68 | 164.59 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_69 | 243.93 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_70 | 266.17 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_71 | 280.86 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_72 | 253.84 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_73 | 2303.38 | True | False | 7 | 7 | 5 | 2 | failed | failed | False | guard_failed, qwen_failed |
| request_74 | 128.86 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_75 | 133.40 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_76 | 139.43 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_77 | 134.87 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_78 | 2246.61 | True | False | 7 | 7 | 5 | 2 | failed | failed | False | guard_failed, qwen_failed |
| request_79 | 228.03 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_80 | 92.75 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_81 | 84.15 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_82 | 148.60 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_83 | 93.69 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_84 | 2656.13 | True | False | 7 | 7 | 5 | 2 | failed | failed | False | guard_failed, qwen_failed |
| request_85 | 87.08 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_86 | 73.11 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_87 | 151.57 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_88 | 93.78 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_89 | 88.62 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_90 | 76.62 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_91 | 264.37 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_92 | 132.03 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_93 | 121.70 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_94 | 262.43 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_95 | 238.21 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_96 | 169.67 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_97 | 157.62 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_98 | 1044.14 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
| request_99 | 472.25 | True | False | 7 | 6 | 5 | 1 | failed | skipped | False | guard_failed |
