import { useContext } from "react";
import { Button } from "./button";
import { AppContext, Params } from "../../context/AppContext";
import { Input } from "./input";
import { Trash2Icon } from "lucide-react";

const InputTemplate = ({ item, type }: { item: Params; type: string }) => {
  const { handleRemove, handleChange } = useContext(AppContext);

  return (
    <div className="input-group my-2 w-full grid grid-cols-7 gap-2">
      <Input
        type="text"
        id="key"
        className="form-control col-span-3"
        placeholder="Key"
        value={item.key}
        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
          handleChange(e, item, type)
        }
      />
      <Input
        type="text"
        id="value"
        className="form-control col-span-3"
        placeholder="Value"
        value={item.value}
        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
          handleChange(e, item, type)
        }
      />
      <Button
        type="button"
        className="col-span-1 bg-transparent border border-red-500 text-red-500 hover:bg-red-500 hover:text-white"
        variant={"outline"}
        onClick={() => handleRemove(item, type)}
      >
        <Trash2Icon size={16} />
      </Button>
    </div>
  );
};

export default InputTemplate;
