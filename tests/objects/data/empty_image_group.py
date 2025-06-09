empty_image_group_ontology = {
    "objects": [
        {"id": "1", "name": "Cars", "color": "#D33115", "shape": "bounding_box", "featureNodeHash": "r4M5dkj7"},
        {"id": "2", "name": "Horses", "color": "#E27300", "shape": "bounding_box", "featureNodeHash": "IuyN9D7S"},
        {"id": "3", "name": "Person", "color": "#16406C", "shape": "bounding_box", "featureNodeHash": "vZSR9ig7"},
        {"id": "4", "name": "Bin", "color": "#FE9200", "shape": "bounding_box", "featureNodeHash": "oYAJdhR1"},
        {"id": "5", "name": "Car segmentation", "color": "#FCDC00", "shape": "polygon", "featureNodeHash": "bPAym0bw"},
        {"id": "6", "name": "Bin", "color": "#DBDF00", "shape": "polygon", "featureNodeHash": "cFwx+HfR"},
        {"id": "7", "name": "Camel", "color": "#A4DD00", "shape": "bounding_box", "featureNodeHash": "oyEb2JCi"},
    ],
    "classifications": [
        {
            "id": "1",
            "featureNodeHash": "6nyvIs5W",
            "attributes": [
                {
                    "id": "1.1",
                    "name": "Is there a car in the frame? SUSPECTED",
                    "type": "radio",
                    "required": False,
                    "dynamic": False,
                    "featureNodeHash": "oehdT/Pe",
                    "options": [
                        {"id": "1.1.1", "label": "True", "value": "true", "featureNodeHash": "F/rpk4Fo"},
                        {"id": "1.1.2", "label": "False", "value": "false", "featureNodeHash": "/ILQSY6c"},
                        {"id": "1.1.3", "label": "Maybe", "value": "maybe", "featureNodeHash": "EDWbo8P8"},
                        {"id": "1.1.4", "label": "Maybe not", "value": "maybe_not", "featureNodeHash": "Uxzj/Efq"},
                        {
                            "id": "1.1.5",
                            "label": "SUSPECTED this is not the case",
                            "value": "suspected_this_is_not_the_case",
                            "featureNodeHash": "ZrRZBwx3",
                        },
                    ],
                }
            ],
        },
        {
            "id": "2",
            "featureNodeHash": "R0SMUli5",
            "attributes": [
                {
                    "id": "2.1",
                    "name": "This is a test",
                    "type": "radio",
                    "required": False,
                    "featureNodeHash": "vDUhRPP0",
                    "options": [
                        {"id": "2.1.1", "label": "Test", "value": "test", "featureNodeHash": "P7BwGqM3"},
                        {"id": "2.1.2", "label": "TEst2", "value": "test2", "featureNodeHash": "+LDYFQp1"},
                    ],
                }
            ],
        },
    ],
}


empty_image_group_labels = {
    "label_hash": "f1e6bc82-9f89-4545-8abb-f271bf28cf99",
    "branch_name": "main",
    "created_at": "Thu, 09 Feb 2023 14:12:03 UTC",
    "last_edited_at": "Thu, 09 Feb 2023 14:12:03 UTC",
    "data_hash": "aaa6bc82-9f89-4545-adbb-f271bf28cf99",
    "annotation_task_status": "QUEUED",
    "is_shadow_data": False,
    "dataset_hash": "d9f19c3c-5cd0-4f8c-b98c-6c0e24676224",
    "dataset_title": "One image group",
    "data_title": "image-group-8375e",
    "data_type": "img_group",
    "data_units": {
        "f850dfb4-7146-49e0-9afc-2b9434a64a9f": {
            "data_hash": "f850dfb4-7146-49e0-9afc-2b9434a64a9f",
            "data_title": "Screenshot 2021-11-24 at 18.35.57.png",
            "data_link": "https://storage.googleapis.com/cord-ai-platform.appspot.com/cord-images-prod/yiA5JxmLEGSoEcJAuxr3AJdDDXE2/f850dfb4-7146-49e0-9afc-2b9434a64a9f?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=firebase-adminsdk-64w1p%40cord-ai-platform.iam.gserviceaccount.com%2F20221201%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20221201T133838Z&X-Goog-Expires=604800&X-Goog-SignedHeaders=host&X-Goog-Signature=94c66d85014ff52a99fec1cf671ccc1b859ebead4308ca82c4d810e13ac285d2afa8cfa4bfcbd09f615b243b95d9b1d5d1d779e7a4ba5832a2207b4f3b99dbe405ded373f03f06abe4e24098e70568c269899f2f397c7a4392a1c3090bff2b8c98f2177f5db36f0884a83033f404354bdfda0506bf162e25ff6186fc54104e8273e86959b0296958a03359514660528a54ba94e25c59e59534ce5102f9c87ff7cb03a591606b3a191123af4a30fa4296a788a9433f0c8c1dc7d3f80a022cc42f8716ba44d09ecd04118dc6e4ee5977ffbadcc8d635cc4e906f024dba26e520cfc304fc0f3458a3e3b2422c196956fd3024a6eba0512d557683487b10a1a381b4",
            "data_type": "image/png",
            "data_sequence": "0",
            "width": 952,
            "height": 678,
            "labels": {
                "objects": [],
                "classifications": [],
            },
        },
        "177d1bb7-5394-4772-ba9f-4569f0c2a995": {
            "data_hash": "177d1bb7-5394-4772-ba9f-4569f0c2a995",
            "data_title": "Screenshot 2021-11-24 at 18.36.02.png",
            "data_link": "https://storage.googleapis.com/cord-ai-platform.appspot.com/cord-images-prod/yiA5JxmLEGSoEcJAuxr3AJdDDXE2/177d1bb7-5394-4772-ba9f-4569f0c2a995?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=firebase-adminsdk-64w1p%40cord-ai-platform.iam.gserviceaccount.com%2F20221201%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20221201T133838Z&X-Goog-Expires=604800&X-Goog-SignedHeaders=host&X-Goog-Signature=808ea15115717eaa939b6b66a74c2d8771216a16d621d7ff8a002e5bec65fcc3053097e2bba0711e3442b4a41afe9744e42ffe6b08194cd83debcf3dbb2d649ab2a92df2b02ed4e77e8eedef577007bb33681410ec164e24ba4c5643df744687762069e9dd360c0fa0820e90cd977d0c199b391e1425dd0e696a517e747b70ed4953f514be87846317c762c519af1f49066797d7a5f9e476bf9abf06e62a3ed5ebcf05516782e2ec913af68a6bedac0349c6b2a528e5411ec96275326c0e67d699cea81eadb6660e31d4a7d611db64b06f67098bad266c7bc6eb6e5191b7a97101a01ffd61b40aaaf24dea2026add406ec362df4df8eac26750b569295c28b86",
            "data_type": "image/png",
            "data_sequence": "1",
            "width": 952,
            "height": 678,
            "labels": {"objects": [], "classifications": []},
        },
        "5f393aff-38e3-4364-8ece-340d5aade1c4": {
            "data_hash": "5f393aff-38e3-4364-8ece-340d5aade1c4",
            "data_title": "Screenshot 2021-11-24 at 18.36.07.png",
            "data_link": "https://storage.googleapis.com/cord-ai-platform.appspot.com/cord-images-prod/yiA5JxmLEGSoEcJAuxr3AJdDDXE2/5f393aff-38e3-4364-8ece-340d5aade1c4?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=firebase-adminsdk-64w1p%40cord-ai-platform.iam.gserviceaccount.com%2F20221201%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20221201T133838Z&X-Goog-Expires=604800&X-Goog-SignedHeaders=host&X-Goog-Signature=8929d2c90b42f74e57fd7b7e2a8e8d9e531d030808c279a2ebb30ddfc589ae4524d28c611fb67b2dfb77a329c2cf48ec21bcc9cbb0d24ac3c822f7c6b47c9f02bf33b45e9e810a500b289d61cd2dec8ea24b8b2d0f5287db8325288f51ac049fd6c3a28c85b29c5ac08634302e7d4c6afaec779d9e11148220f5412532ff152c36055a5fd197c8bdd3fe5471c36c061cf52c91607a5bb9a07a17aa352a59a170a3be7e4010123622d7a82b5714cc9b2a47bc320938973911e760e2b6d919ccfdf3da6cafdfedb888989ad1306581f30c287259fdf1a29c69b34b6ec4a91d332356c918281bac45ef8ff3665a3b1b0990b225d588b7897097a06136a5dd1bbbc7",
            "data_type": "image/png",
            "data_sequence": "2",
            "width": 952,
            "height": 678,
            "labels": {"objects": [], "classifications": []},
        },
        "6518e742-8dee-4a6d-b491-710f8a5c0fc4": {
            "data_hash": "6518e742-8dee-4a6d-b491-710f8a5c0fc4",
            "data_title": "Screenshot 2021-11-24 at 18.36.11.png",
            "data_link": "https://storage.googleapis.com/cord-ai-platform.appspot.com/cord-images-prod/yiA5JxmLEGSoEcJAuxr3AJdDDXE2/6518e742-8dee-4a6d-b491-710f8a5c0fc4?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=firebase-adminsdk-64w1p%40cord-ai-platform.iam.gserviceaccount.com%2F20221201%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20221201T133838Z&X-Goog-Expires=604800&X-Goog-SignedHeaders=host&X-Goog-Signature=001d6367d2bba32a7483a5217e06a5b1855fe0ddc18d0a2e33482afec25f5f2841f352e115c8d63d38f306b2514e19e021436e0bcc83177a85802d28fbe08f6bd6021331c5ca5cce3f7383a9190f56748378880a1b35d4ab0913716727c10214a11989fbcc6e3b52b0b4df382562c93ffb175ba3e87ce4a1494c5739b716a5ff0b4570bd69074642f0960f1ecfa333312accb1283016ba427749fa2129ac36927304f0fd5b722850084521b874fd53e63fd7dab25fcd20e7caf7fa3021f13b8b7ef0747c36848f6fe3f727937ed6f0243ad1e69d3d46213b6735c349f498534d7c55a106ae61042128fe7d80e4773897f28957d346844bea82b845e4856309ff",
            "data_type": "image/png",
            "data_sequence": "3",
            "width": 952,
            "height": 678,
            "labels": {"objects": [], "classifications": []},
        },
        "24dd04ee-ff3f-4f91-b6b5-b385defc7307": {
            "data_hash": "24dd04ee-ff3f-4f91-b6b5-b385defc7307",
            "data_title": "Screenshot 2021-11-24 at 18.36.19.png",
            "data_link": "https://storage.googleapis.com/cord-ai-platform.appspot.com/cord-images-prod/yiA5JxmLEGSoEcJAuxr3AJdDDXE2/24dd04ee-ff3f-4f91-b6b5-b385defc7307?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=firebase-adminsdk-64w1p%40cord-ai-platform.iam.gserviceaccount.com%2F20221201%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20221201T133838Z&X-Goog-Expires=604800&X-Goog-SignedHeaders=host&X-Goog-Signature=4574efaee32c7f3aa37fb5d5e47718e79685b802c9563861bfc057c25c8e3d85672fe04daaa694b39d3ebc6f60589c68e8ccf810d05f896896136cf178eb5a24ebb67b37501ce78c37b3618b1cde1a515ff8e07d9c6d9afb6476d4d792845ea954251c3383dd56b0d76d62be55644df2eeb36c9db06fb01e905a8659b1e8170344dcd1c65ac001e5e3e38ae49cd0aa5780681901177b0b0743d67b3b28ac698590e53a7b3ae2da6f9bbb1e2c15600a1d5a249b7fddbb7ee92f7a0684a71d6b7919f5cb2f9171e1dd47afb04775f3153b265f78f3b74355057c68c7e40ca12b50880925029d51e014c5a15bd1e8d40921f69dca5764e2bedc472c6915789b8b8b",
            "data_type": "image/png",
            "data_sequence": "4",
            "width": 952,
            "height": 678,
            "labels": {"objects": [], "classifications": []},
        },
    },
    "object_answers": {},
    "classification_answers": {},
    "object_actions": {},
    "label_status": "LABEL_IN_PROGRESS",
}
