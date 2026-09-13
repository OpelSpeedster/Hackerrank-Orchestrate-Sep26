# Model Usage and Evaluation Report

Output: `/projects/challenge/output.csv`

## Providers and models

- Provider: `Groq`
- Qwen extraction model: `qwen/qwen3.8-27b`
- Meta safety/router model: `meta-llama/llama-prompt-guard-2-86m`
- Modal is optional and is used only when `MODAL_API_KEY` and `MODAL_ENDPOINT` are configured.

## Requests and latency

- Requests processed: 250
- Valid requests: 250
- Fallback requests: 0
- Average latency (ms): 1420.46
- P50 latency (ms): 78.88
- P95 latency (ms): 297.21

## Model usage

- Total model calls: 261
- Llama/Meta safety calls: 250
- Qwen image extraction calls: 11
- Failed model calls: 254
- Timed-out model calls: 4
- Input tokens: 11127
- Output tokens: 970
- Total tokens: 12097
- Estimated provider cost (USD): 0.01278160
- Estimated cost per request (USD): 0.00005113

## Safety metrics

- Completed safety calls: 0
- Flagged requests: 0
- Safety flag rate: 0.0000%

## Per-request latency

| request_id | latency_ms | valid | fallback | guard_status | guard_flagged | tool_calls | errors |
|---|---:|---:|---:|---|---:|---:|---|
| request_100 | 64.41 | True | False | unavailable | False | 7 |  |
| request_101 | 49431.61 | True | False | unavailable | False | 7 |  |
| request_102 | 135.23 | True | False | unavailable | False | 7 |  |
| request_103 | 74.01 | True | False | unavailable | False | 7 |  |
| request_104 | 70.59 | True | False | unavailable | False | 7 |  |
| request_105 | 27571.07 | True | False | unavailable | False | 7 |  |
| request_106 | 64.39 | True | False | unavailable | False | 7 |  |
| request_107 | 77.58 | True | False | unavailable | False | 7 |  |
| request_108 | 72.82 | True | False | unavailable | False | 7 |  |
| request_109 | 82.20 | True | False | unavailable | False | 7 |  |
| request_110 | 54.34 | True | False | unavailable | False | 7 |  |
| request_111 | 57.62 | True | False | unavailable | False | 7 |  |
| request_112 | 78.06 | True | False | unavailable | False | 7 |  |
| request_113 | 38549.35 | True | False | unavailable | False | 7 |  |
| request_114 | 58.93 | True | False | unavailable | False | 7 |  |
| request_115 | 61.58 | True | False | unavailable | False | 7 |  |
| request_116 | 81.44 | True | False | unavailable | False | 7 |  |
| request_117 | 70.20 | True | False | unavailable | False | 7 |  |
| request_118 | 87.14 | True | False | unavailable | False | 7 |  |
| request_119 | 76.47 | True | False | unavailable | False | 7 |  |
| request_120 | 55.33 | True | False | unavailable | False | 7 |  |
| request_121 | 58.67 | True | False | unavailable | False | 7 |  |
| request_122 | 60.69 | True | False | unavailable | False | 7 |  |
| request_123 | 56.59 | True | False | unavailable | False | 7 |  |
| request_124 | 60.99 | True | False | unavailable | False | 7 |  |
| request_125 | 82.55 | True | False | unavailable | False | 7 |  |
| request_126 | 67.28 | True | False | unavailable | False | 7 |  |
| request_127 | 79.40 | True | False | unavailable | False | 7 |  |
| request_128 | 75.68 | True | False | unavailable | False | 7 |  |
| request_129 | 69.16 | True | False | unavailable | False | 7 |  |
| request_130 | 67.76 | True | False | unavailable | False | 7 |  |
| request_131 | 73.69 | True | False | unavailable | False | 7 |  |
| request_132 | 63.91 | True | False | unavailable | False | 7 |  |
| request_133 | 54.06 | True | False | unavailable | False | 7 |  |
| request_134 | 56.80 | True | False | unavailable | False | 7 |  |
| request_135 | 55.59 | True | False | unavailable | False | 7 |  |
| request_136 | 54.10 | True | False | unavailable | False | 7 |  |
| request_137 | 71.54 | True | False | unavailable | False | 7 |  |
| request_138 | 73.36 | True | False | unavailable | False | 7 |  |
| request_139 | 63.65 | True | False | unavailable | False | 7 |  |
| request_140 | 78.88 | True | False | unavailable | False | 7 |  |
| request_141 | 166.41 | True | False | unavailable | False | 7 |  |
| request_142 | 66.93 | True | False | unavailable | False | 7 |  |
| request_143 | 68.02 | True | False | unavailable | False | 7 |  |
| request_144 | 92.97 | True | False | unavailable | False | 7 |  |
| request_145 | 78.86 | True | False | unavailable | False | 7 |  |
| request_146 | 69.94 | True | False | unavailable | False | 7 |  |
| request_147 | 67.75 | True | False | unavailable | False | 7 |  |
| request_148 | 115.04 | True | False | unavailable | False | 7 |  |
| request_149 | 62.25 | True | False | unavailable | False | 7 |  |
| request_150 | 84.63 | True | False | unavailable | False | 7 |  |
| request_151 | 55.18 | True | False | unavailable | False | 7 |  |
| request_152 | 85.73 | True | False | unavailable | False | 7 |  |
| request_153 | 83.01 | True | False | unavailable | False | 7 |  |
| request_154 | 75.90 | True | False | unavailable | False | 7 |  |
| request_155 | 71.82 | True | False | unavailable | False | 7 |  |
| request_156 | 65.35 | True | False | unavailable | False | 7 |  |
| request_157 | 71.14 | True | False | unavailable | False | 7 |  |
| request_158 | 55.27 | True | False | unavailable | False | 7 |  |
| request_159 | 54.91 | True | False | unavailable | False | 7 |  |
| request_160 | 67.03 | True | False | unavailable | False | 7 |  |
| request_161 | 78.82 | True | False | unavailable | False | 7 |  |
| request_162 | 70.51 | True | False | unavailable | False | 7 |  |
| request_163 | 69.82 | True | False | unavailable | False | 7 |  |
| request_164 | 73.85 | True | False | unavailable | False | 7 |  |
| request_165 | 56.19 | True | False | unavailable | False | 7 |  |
| request_166 | 56.99 | True | False | unavailable | False | 7 |  |
| request_167 | 55.69 | True | False | unavailable | False | 7 |  |
| request_168 | 132.51 | True | False | unavailable | False | 7 |  |
| request_169 | 82.50 | True | False | unavailable | False | 7 |  |
| request_170 | 119.63 | True | False | unavailable | False | 7 |  |
| request_171 | 96.06 | True | False | unavailable | False | 7 |  |
| request_172 | 54.90 | True | False | unavailable | False | 7 |  |
| request_173 | 81.76 | True | False | unavailable | False | 7 |  |
| request_174 | 57.11 | True | False | unavailable | False | 7 |  |
| request_175 | 56.27 | True | False | unavailable | False | 7 |  |
| request_176 | 76.51 | True | False | unavailable | False | 7 |  |
| request_177 | 56.80 | True | False | unavailable | False | 7 |  |
| request_178 | 79.62 | True | False | unavailable | False | 7 |  |
| request_179 | 66.53 | True | False | unavailable | False | 7 |  |
| request_180 | 75.71 | True | False | unavailable | False | 7 |  |
| request_181 | 75.84 | True | False | unavailable | False | 7 |  |
| request_182 | 59.45 | True | False | unavailable | False | 7 |  |
| request_183 | 84.39 | True | False | unavailable | False | 7 |  |
| request_184 | 79.15 | True | False | unavailable | False | 7 |  |
| request_185 | 71.36 | True | False | unavailable | False | 7 |  |
| request_186 | 73.16 | True | False | unavailable | False | 7 |  |
| request_187 | 60.27 | True | False | unavailable | False | 7 |  |
| request_188 | 72.53 | True | False | unavailable | False | 7 |  |
| request_189 | 54.32 | True | False | unavailable | False | 7 |  |
| request_190 | 55.36 | True | False | unavailable | False | 7 |  |
| request_191 | 57.07 | True | False | unavailable | False | 7 |  |
| request_192 | 67.72 | True | False | unavailable | False | 7 |  |
| request_193 | 171.70 | True | False | unavailable | False | 7 |  |
| request_194 | 66.88 | True | False | unavailable | False | 7 |  |
| request_195 | 86.22 | True | False | unavailable | False | 7 |  |
| request_196 | 54.29 | True | False | unavailable | False | 7 |  |
| request_197 | 74.31 | True | False | unavailable | False | 7 |  |
| request_198 | 67.46 | True | False | unavailable | False | 7 |  |
| request_199 | 63.67 | True | False | unavailable | False | 7 |  |
| request_200 | 71.85 | True | False | unavailable | False | 7 |  |
| request_201 | 54.70 | True | False | unavailable | False | 7 |  |
| request_202 | 54.35 | True | False | unavailable | False | 7 |  |
| request_203 | 56.97 | True | False | unavailable | False | 7 |  |
| request_204 | 77.27 | True | False | unavailable | False | 7 |  |
| request_205 | 57.49 | True | False | unavailable | False | 7 |  |
| request_206 | 58.88 | True | False | unavailable | False | 7 |  |
| request_207 | 57.44 | True | False | unavailable | False | 7 |  |
| request_208 | 55.93 | True | False | unavailable | False | 7 |  |
| request_209 | 68.89 | True | False | unavailable | False | 7 |  |
| request_210 | 74.29 | True | False | unavailable | False | 7 |  |
| request_211 | 58.75 | True | False | unavailable | False | 7 |  |
| request_212 | 137.07 | True | False | unavailable | False | 7 |  |
| request_213 | 66.75 | True | False | unavailable | False | 7 |  |
| request_214 | 81.13 | True | False | unavailable | False | 7 |  |
| request_215 | 56.05 | True | False | unavailable | False | 7 |  |
| request_216 | 69.92 | True | False | unavailable | False | 7 |  |
| request_217 | 72.94 | True | False | unavailable | False | 7 |  |
| request_218 | 56.43 | True | False | unavailable | False | 7 |  |
| request_219 | 69.09 | True | False | unavailable | False | 7 |  |
| request_220 | 218.22 | True | False | unavailable | False | 7 |  |
| request_221 | 52.88 | True | False | unavailable | False | 7 |  |
| request_222 | 54.15 | True | False | unavailable | False | 7 |  |
| request_223 | 54.63 | True | False | unavailable | False | 7 |  |
| request_224 | 152.18 | True | False | unavailable | False | 7 |  |
| request_225 | 129.55 | True | False | unavailable | False | 7 |  |
| request_226 | 69.41 | True | False | unavailable | False | 7 |  |
| request_227 | 71.95 | True | False | unavailable | False | 7 |  |
| request_228 | 166.25 | True | False | unavailable | False | 7 |  |
| request_229 | 136.02 | True | False | unavailable | False | 7 |  |
| request_230 | 124.87 | True | False | unavailable | False | 7 |  |
| request_231 | 132.83 | True | False | unavailable | False | 7 |  |
| request_232 | 134.70 | True | False | unavailable | False | 7 |  |
| request_233 | 125.20 | True | False | unavailable | False | 7 |  |
| request_234 | 114.09 | True | False | unavailable | False | 7 |  |
| request_235 | 164.41 | True | False | unavailable | False | 7 |  |
| request_236 | 187.76 | True | False | unavailable | False | 7 |  |
| request_237 | 132.18 | True | False | unavailable | False | 7 |  |
| request_238 | 102.82 | True | False | unavailable | False | 7 |  |
| request_239 | 125.95 | True | False | unavailable | False | 7 |  |
| request_240 | 123.11 | True | False | unavailable | False | 7 |  |
| request_241 | 109.97 | True | False | unavailable | False | 7 |  |
| request_242 | 112.75 | True | False | unavailable | False | 7 |  |
| request_243 | 99.37 | True | False | unavailable | False | 7 |  |
| request_244 | 119.12 | True | False | unavailable | False | 7 |  |
| request_245 | 179.29 | True | False | unavailable | False | 7 |  |
| request_246 | 117.22 | True | False | unavailable | False | 7 |  |
| request_247 | 88.09 | True | False | unavailable | False | 7 |  |
| request_248 | 131.34 | True | False | unavailable | False | 7 |  |
| request_249 | 108.23 | True | False | unavailable | False | 7 |  |
| request_250 | 165.13 | True | False | unavailable | False | 7 |  |
| request_251 | 107.77 | True | False | unavailable | False | 7 |  |
| request_252 | 104.52 | True | False | unavailable | False | 7 |  |
| request_253 | 215.32 | True | False | unavailable | False | 7 |  |
| request_254 | 155.20 | True | False | unavailable | False | 7 |  |
| request_255 | 101.68 | True | False | unavailable | False | 7 |  |
| request_256 | 109.99 | True | False | unavailable | False | 7 |  |
| request_257 | 144.31 | True | False | unavailable | False | 7 |  |
| request_258 | 123.58 | True | False | unavailable | False | 7 |  |
| request_259 | 120.61 | True | False | unavailable | False | 7 |  |
| request_26 | 250.71 | True | False | unavailable | False | 7 |  |
| request_260 | 122.98 | True | False | unavailable | False | 7 |  |
| request_261 | 128.52 | True | False | unavailable | False | 7 |  |
| request_262 | 125.55 | True | False | unavailable | False | 7 |  |
| request_263 | 126.55 | True | False | unavailable | False | 7 |  |
| request_264 | 116.29 | True | False | unavailable | False | 7 |  |
| request_265 | 89.14 | True | False | unavailable | False | 7 |  |
| request_266 | 83.02 | True | False | unavailable | False | 7 |  |
| request_267 | 133.65 | True | False | unavailable | False | 7 |  |
| request_268 | 129.86 | True | False | unavailable | False | 7 |  |
| request_269 | 127.80 | True | False | unavailable | False | 7 |  |
| request_27 | 157.58 | True | False | unavailable | False | 7 |  |
| request_270 | 127.66 | True | False | unavailable | False | 7 |  |
| request_271 | 125.96 | True | False | unavailable | False | 7 |  |
| request_272 | 125.80 | True | False | unavailable | False | 7 |  |
| request_273 | 128.48 | True | False | unavailable | False | 7 |  |
| request_274 | 131.71 | True | False | unavailable | False | 7 |  |
| request_275 | 57.98 | True | False | unavailable | False | 7 |  |
| request_28 | 297.21 | True | False | unavailable | False | 7 |  |
| request_29 | 240.95 | True | False | unavailable | False | 7 |  |
| request_30 | 274.89 | True | False | unavailable | False | 7 |  |
| request_31 | 196.10 | True | False | unavailable | False | 7 |  |
| request_32 | 302.00 | True | False | unavailable | False | 7 |  |
| request_33 | 1161.33 | True | False | unavailable | False | 7 |  |
| request_34 | 138.38 | True | False | unavailable | False | 7 |  |
| request_35 | 1183.31 | True | False | unavailable | False | 7 |  |
| request_36 | 141.99 | True | False | unavailable | False | 7 |  |
| request_37 | 124.47 | True | False | unavailable | False | 7 |  |
| request_38 | 123.82 | True | False | unavailable | False | 7 |  |
| request_39 | 120.14 | True | False | unavailable | False | 7 |  |
| request_40 | 133.96 | True | False | unavailable | False | 7 |  |
| request_41 | 133.99 | True | False | unavailable | False | 7 |  |
| request_42 | 166.18 | True | False | unavailable | False | 7 |  |
| request_43 | 126.69 | True | False | unavailable | False | 7 |  |
| request_44 | 120.96 | True | False | unavailable | False | 7 |  |
| request_45 | 105.75 | True | False | unavailable | False | 7 |  |
| request_46 | 178.64 | True | False | unavailable | False | 7 |  |
| request_47 | 242.68 | True | False | unavailable | False | 7 |  |
| request_48 | 30501.00 | True | False | unavailable | False | 7 |  |
| request_49 | 236.58 | True | False | unavailable | False | 7 |  |
| request_50 | 214.55 | True | False | unavailable | False | 7 |  |
| request_51 | 121.57 | True | False | unavailable | False | 7 |  |
| request_52 | 121.23 | True | False | unavailable | False | 7 |  |
| request_53 | 237.74 | True | False | unavailable | False | 7 |  |
| request_54 | 207.91 | True | False | unavailable | False | 7 |  |
| request_55 | 19764.41 | True | False | unavailable | False | 7 |  |
| request_56 | 121.58 | True | False | unavailable | False | 7 |  |
| request_57 | 103.97 | True | False | unavailable | False | 7 |  |
| request_58 | 115.25 | True | False | unavailable | False | 7 |  |
| request_59 | 111.53 | True | False | unavailable | False | 7 |  |
| request_60 | 91.72 | True | False | unavailable | False | 7 |  |
| request_61 | 87.95 | True | False | unavailable | False | 7 |  |
| request_62 | 113.53 | True | False | unavailable | False | 7 |  |
| request_63 | 116.08 | True | False | unavailable | False | 7 |  |
| request_64 | 49217.37 | True | False | unavailable | False | 7 |  |
| request_65 | 137.37 | True | False | unavailable | False | 7 |  |
| request_66 | 53.19 | True | False | unavailable | False | 7 |  |
| request_67 | 57.46 | True | False | unavailable | False | 7 |  |
| request_68 | 85.02 | True | False | unavailable | False | 7 |  |
| request_69 | 54.90 | True | False | unavailable | False | 7 |  |
| request_70 | 63.25 | True | False | unavailable | False | 7 |  |
| request_71 | 84.35 | True | False | unavailable | False | 7 |  |
| request_72 | 77.21 | True | False | unavailable | False | 7 |  |
| request_73 | 37497.26 | True | False | unavailable | False | 7 |  |
| request_74 | 68.37 | True | False | unavailable | False | 7 |  |
| request_75 | 55.56 | True | False | unavailable | False | 7 |  |
| request_76 | 75.45 | True | False | unavailable | False | 7 |  |
| request_77 | 55.98 | True | False | unavailable | False | 7 |  |
| request_78 | 49032.34 | True | False | unavailable | False | 7 |  |
| request_79 | 77.13 | True | False | unavailable | False | 7 |  |
| request_80 | 78.39 | True | False | unavailable | False | 7 |  |
| request_81 | 53.95 | True | False | unavailable | False | 7 |  |
| request_82 | 68.72 | True | False | unavailable | False | 7 |  |
| request_83 | 69.93 | True | False | unavailable | False | 7 |  |
| request_84 | 28036.88 | True | False | unavailable | False | 7 |  |
| request_85 | 72.44 | True | False | unavailable | False | 7 |  |
| request_86 | 58.58 | True | False | unavailable | False | 7 |  |
| request_87 | 88.58 | True | False | unavailable | False | 7 |  |
| request_88 | 76.20 | True | False | unavailable | False | 7 |  |
| request_89 | 70.66 | True | False | unavailable | False | 7 |  |
| request_90 | 64.51 | True | False | unavailable | False | 7 |  |
| request_91 | 72.58 | True | False | unavailable | False | 7 |  |
| request_92 | 92.93 | True | False | unavailable | False | 7 |  |
| request_93 | 53.64 | True | False | unavailable | False | 7 |  |
| request_94 | 65.80 | True | False | unavailable | False | 7 |  |
| request_95 | 67.68 | True | False | unavailable | False | 7 |  |
| request_96 | 73.74 | True | False | unavailable | False | 7 |  |
| request_97 | 59.48 | True | False | unavailable | False | 7 |  |
| request_98 | 81.54 | True | False | unavailable | False | 7 |  |
| request_99 | 55.93 | True | False | unavailable | False | 7 |  |
