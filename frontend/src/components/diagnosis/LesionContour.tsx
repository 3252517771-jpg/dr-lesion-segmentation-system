import { Empty } from "antd";

interface LesionContourProps {
  imageUrl?: string | null;
}

export default function LesionContour({ imageUrl }: LesionContourProps) {
  if (!imageUrl) {
    return <Empty description="暂无轮廓图" />;
  }
  return <img className="image-preview" src={imageUrl} alt="病灶轮廓叠加图" />;
}
