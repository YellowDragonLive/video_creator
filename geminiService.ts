
import { GoogleGenAI, Type, GenerateContentResponse } from "@google/genai";
import { Shot } from "../types";

export const checkApiKey = async (): Promise<boolean> => {
  if (typeof window.aistudio?.hasSelectedApiKey === 'function') {
    const hasKey = await window.aistudio.hasSelectedApiKey();
    if (!hasKey) {
      if (typeof window.aistudio.openSelectKey === 'function') {
        await window.aistudio.openSelectKey();
        return true;
      }
    }
    return true;
  }
  return true;
};

const getAIClient = () => {
  const apiKey = process.env.API_KEY;
  if (!apiKey) throw new Error("API Key is missing from environment.");
  return new GoogleGenAI({ apiKey });
};

/**
 * 深度解析镜头：双语提示词反推 + 运动轨迹 + 风格标签
 */
export const analyzeVideoShots = async (frames: string[]): Promise<Shot[]> => {
  const ai = getAIClient();
  
  const contents = {
    parts: [
      { text: `你是一位顶级广告视觉创意师。请深度解析以下视频关键帧，并为每个镜头提供：
1. **中英文提示词反推**：详细描述画面（主体、材质、光影、环境）。英文用于 AI 生成，中文供用户理解。
2. **运镜与转场**：描述相机的动态和剪辑节奏。
3. **视觉风格标签**：提取如 "Cinematic Lighting", "Golden Hour", "Macro" 等核心风格词。

请以 JSON 格式返回，包含一个 shots 数组，字段：
id, startTime, endTime, originalPromptEn, originalPromptZh, transitionType, motionDescription, styleTags(数组)。` },
      ...frames.map(frame => ({
        inlineData: {
          mimeType: "image/jpeg",
          data: frame.split(',')[1]
        }
      }))
    ]
  };

  const response = await ai.models.generateContent({
    model: 'gemini-3-pro-preview',
    contents: [contents],
    config: {
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          shots: {
            type: Type.ARRAY,
            items: {
              type: Type.OBJECT,
              properties: {
                id: { type: Type.STRING },
                startTime: { type: Type.NUMBER },
                endTime: { type: Type.NUMBER },
                originalPromptEn: { type: Type.STRING },
                originalPromptZh: { type: Type.STRING },
                transitionType: { type: Type.STRING },
                motionDescription: { type: Type.STRING },
                styleTags: { type: Type.ARRAY, items: { type: Type.STRING } }
              },
              required: ["id", "startTime", "endTime", "originalPromptEn", "originalPromptZh", "transitionType", "motionDescription", "styleTags"]
            }
          }
        },
        required: ["shots"]
      }
    }
  });

  try {
    const data = JSON.parse(response.text || "{}");
    return data.shots.map((s: any, idx: number) => ({
      ...s,
      targetPromptEn: s.originalPromptEn,
      targetPromptZh: s.originalPromptZh,
      thumbnail: frames[Math.min(idx, frames.length - 1)]
    }));
  } catch (e) {
    console.error("Analysis failed", e);
    return [];
  }
};

/**
 * 视觉重塑：融合品牌资产特征与参考风格，输出双语提示词
 */
export interface RefinedPromptResult {
  promptEn: string;
  promptZh: string;
}

export const refineBrandPromptBilingual = async (originalPromptEn: string, brandImageBase64: string): Promise<RefinedPromptResult> => {
  const ai = getAIClient();
  const response = await ai.models.generateContent({
    model: 'gemini-3-pro-preview',
    contents: [
      {
        parts: [
          { inlineData: { mimeType: "image/png", data: brandImageBase64.split(',')[1] } },
          { text: `这是用户的品牌资产（产品或主角）。原片风格描述为：“${originalPromptEn}”。
请进行“视觉修正”：
1. 分析品牌资产的特征。
2. 生成一段英文提示词（promptEn），将品牌资产自然融入原片光影、材质与构图（例如：为白底产品添加原片同款的霓虹反射）。
3. 生成对应的中文解释（promptZh）。
请以 JSON 格式返回：{ "promptEn": "...", "promptZh": "..." }。` }
        ]
      }
    ],
    config: {
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          promptEn: { type: Type.STRING },
          promptZh: { type: Type.STRING }
        },
        required: ["promptEn", "promptZh"]
      }
    }
  });

  try {
    return JSON.parse(response.text || "{}") as RefinedPromptResult;
  } catch (e) {
    return { promptEn: originalPromptEn, promptZh: "同步失败" };
  }
};

/**
 * 视觉对齐：使用 Banana Pro (gemini-3-pro-image-preview) 重新生成符合氛围的产品图
 */
export const generateRefinedBrandImage = async (promptEn: string, brandImageBase64: string): Promise<string> => {
  const ai = getAIClient();
  const response = await ai.models.generateContent({
    model: 'gemini-3-pro-image-preview',
    contents: {
      parts: [
        {
          inlineData: {
            mimeType: 'image/png',
            data: brandImageBase64.split(',')[1],
          },
        },
        {
          text: `Please redraw or modify the product in the provided image to perfectly match this environment description: "${promptEn}". Keep the original product's identity clear but apply the cinematic lighting, reflections, and composition mentioned in the prompt. Output the new image.`,
        },
      ],
    },
    config: {
      imageConfig: {
        aspectRatio: "16:9",
        imageSize: "1K"
      },
    },
  });

  for (const part of response.candidates?.[0]?.content?.parts || []) {
    if (part.inlineData) {
      return `data:image/png;base64,${part.inlineData.data}`;
    }
  }
  throw new Error("No image data returned from AI");
};

/**
 * 调用 Veo 3.1 渲染
 */
export const generateShotVideo = async (shot: Shot, aspectRatio: "16:9" | "9:16" = "16:9"): Promise<string> => {
  const ai = getAIClient();
  
  try {
    const config: any = {
      model: 'veo-3.1-fast-generate-preview',
      prompt: shot.targetPromptEn, 
      config: {
        numberOfVideos: 1,
        resolution: '720p',
        aspectRatio: aspectRatio
      }
    };

    if (shot.brandImage) {
      config.image = {
        imageBytes: shot.brandImage.split(',')[1],
        mimeType: shot.brandImageMimeType || 'image/png'
      };
    }

    let operation = await ai.models.generateVideos(config);

    while (!operation.done) {
      await new Promise(resolve => setTimeout(resolve, 5000));
      operation = await ai.operations.getVideosOperation({ operation: operation });
    }

    const downloadLink = operation.response?.generatedVideos?.[0]?.video?.uri;
    if (!downloadLink) throw new Error("Video generation failed");
    
    const response = await fetch(`${downloadLink}&key=${process.env.API_KEY}`);
    const blob = await response.blob();
    return URL.createObjectURL(blob);
  } catch (error: any) {
    if (error.message?.includes("Requested entity was not found")) {
      await window.aistudio?.openSelectKey?.();
    }
    throw error;
  }
};
