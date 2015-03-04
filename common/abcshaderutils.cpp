#include "abcshaderutils.h"

void setUserParameter(AtNode* source, std::string interfaceName, Alembic::AbcCoreAbstract::PropertyHeader header, AtNode* node)
{
    if (Abc::IFloatProperty::matches(header))
    {
        // float type
        AiNodeSetFlt(node, header.getName().c_str(), AiNodeGetFlt(source, interfaceName.c_str()));
    }
    else if (Abc::IInt32Property::matches(header))
    {
        // int type
        AiNodeSetInt(node, header.getName().c_str(), AiNodeGetInt(source, interfaceName.c_str()));
    }
    else if (Abc::IUInt32Property::matches(header))
    {
        // Uint type
        AiNodeSetUInt(node, header.getName().c_str(), AiNodeGetUInt(source, interfaceName.c_str()));
    }
    else if (Abc::IBoolProperty::matches(header))
    {
        // bool type
        AiNodeSetBool(node, header.getName().c_str(), AiNodeGetBool(source, interfaceName.c_str()));
    }
    else if (Abc::IStringProperty::matches(header))
    {
        // string type
        AiNodeSetStr(node, header.getName().c_str(), AiNodeGetStr(source, interfaceName.c_str()));
    }
    else if (Abc::IP3fProperty::matches(header))
    {
        // point type
        // We don't really have point type in maya, so the source is a vector.
        AtVector val = AiNodeGetVec(source, interfaceName.c_str());
        AiNodeSetPnt(node, header.getName().c_str(), val.x, val.y, val.z);
    }
    else if (Abc::IV3fProperty::matches(header))
    {
        // vector type
        AtVector val = AiNodeGetVec(source, interfaceName.c_str());
        AiNodeSetVec(node, header.getName().c_str(), val.x, val.y, val.z);
    }
    else if (Abc::IC3fProperty::matches(header))
    {
        // color type
        AtColor val = AiNodeGetRGB(source, interfaceName.c_str());
        AiNodeSetRGB(node, header.getName().c_str(), val.r, val.g, val.b);
    }
}

void setArrayParameter(Alembic::Abc::ICompoundProperty props, Alembic::AbcCoreAbstract::PropertyHeader header, AtNode* node)
{

    AtArray *arrayValues;


    if (Abc::IFloatArrayProperty::matches(header))
    {
        // float type

        Abc::FloatArraySamplePtr samp;
        Abc::IFloatArrayProperty prop(props, header.getName());
        if (prop.valid())
        {
            size_t numSamples = prop.getNumSamples();
            if (numSamples > 0)
            {
                prop.get( samp, Alembic::Abc::ISampleSelector((Alembic::Abc::index_t)0) );
                arrayValues = AiArrayAllocate(samp->size(), numSamples, AI_TYPE_FLOAT);
                for( int i = 0; i < samp->size(); ++i )
                {
                    AiArraySetFlt(arrayValues, i, (*samp)[i]);
                }

                AiNodeSetArray(node, header.getName().c_str(), arrayValues);
            }
        }


    }
    else if (Abc::IInt32ArrayProperty::matches(header))
    {
        // int type
        Abc::Int32ArraySamplePtr samp;
        Abc::IInt32ArrayProperty prop(props, header.getName());
        if (prop.valid())
        {
            size_t numSamples = prop.getNumSamples();
            if (numSamples > 0)
            {
                prop.get( samp, Alembic::Abc::ISampleSelector((Alembic::Abc::index_t)0) );
                arrayValues = AiArrayAllocate(samp->size(), numSamples, AI_TYPE_INT);
                for( int i = 0; i < samp->size(); ++i )
                {
                    AiArraySetInt(arrayValues, i, (*samp)[i]);
                }

                AiNodeSetArray(node, header.getName().c_str(), arrayValues);
            }
        }
    }
    else if (Abc::IBoolArrayProperty::matches(header))
    {
        // bool type
        Abc::BoolArraySamplePtr samp;
        Abc::IBoolArrayProperty prop(props, header.getName());
        if (prop.valid())
        {
            size_t numSamples = prop.getNumSamples();
            if (numSamples > 0)
            {
                prop.get( samp, Alembic::Abc::ISampleSelector((Alembic::Abc::index_t)0) );
                arrayValues = AiArrayAllocate(samp->size(), numSamples, AI_TYPE_BOOLEAN);
                for( int i = 0; i < samp->size(); ++i )
                {
                    AiArraySetBool(arrayValues, i, (*samp)[i]);
                }

                AiNodeSetArray(node, header.getName().c_str(), arrayValues);
            }
        }
    }
    else if (Abc::IStringArrayProperty::matches(header))
    {
        // string type
        Abc::StringArraySamplePtr samp;
        Abc::IStringArrayProperty prop(props, header.getName());
        if (prop.valid())
        {
            size_t numSamples = prop.getNumSamples();
            if (numSamples > 0)
            {
                prop.get( samp, Alembic::Abc::ISampleSelector((Alembic::Abc::index_t)0) );
                arrayValues = AiArrayAllocate(samp->size(), numSamples, AI_TYPE_STRING);
                for( int i = 0; i < samp->size(); ++i )
                {
                    AiArraySetStr(arrayValues, i, (*samp)[i].c_str());
                }

                AiNodeSetArray(node, header.getName().c_str(), arrayValues);
            }
        }
    }

    else if (Abc::IV3fArrayProperty::matches(header))
    {
        // vector type
        Abc::V3fArraySamplePtr samp;
        Abc::IV3fArrayProperty prop(props, header.getName());
        if (prop.valid())
        {
            size_t numSamples = prop.getNumSamples();
            if (numSamples > 0)
            {
                prop.get( samp, Alembic::Abc::ISampleSelector((Alembic::Abc::index_t)0) );
                arrayValues = AiArrayAllocate(samp->size(), numSamples, AI_TYPE_VECTOR);
                for( int i = 0; i < samp->size(); ++i)
                {
                    AtVector val;
                    val.x = (*samp)[i].x;
                    val.y = (*samp)[i].y;
                    val.z = (*samp)[i].z;
                    AiArraySetVec(arrayValues,i, val);

                }
                AiNodeSetArray(node, header.getName().c_str(), arrayValues);
            }
        }
    }
    else if (Abc::IP3fArrayProperty::matches(header))
    {
        // point type
        Abc::P3fArraySamplePtr samp;
        Abc::IP3fArrayProperty prop(props, header.getName());
        if (prop.valid())
        {
            size_t numSamples = prop.getNumSamples();
            if (numSamples > 0)
            {
                prop.get( samp, Alembic::Abc::ISampleSelector((Alembic::Abc::index_t)0) );
                arrayValues = AiArrayAllocate(samp->size(), numSamples, AI_TYPE_POINT);
                for( int i = 0; i < samp->size(); ++i)
                {
                    AtPoint val;
                    val.x = (*samp)[i].x;
                    val.y = (*samp)[i].y;
                    val.z = (*samp)[i].z;
                    AiArraySetPnt(arrayValues,i, val);

                }
                AiNodeSetArray(node, header.getName().c_str(), arrayValues);
            }
        }
    }
    else if (Abc::IC3fArrayProperty::matches(header))
    {
        // color type
        Abc::C3fArraySamplePtr samp;
        Abc::IC3fArrayProperty prop(props, header.getName());
        if (prop.valid())
        {
            size_t numSamples = prop.getNumSamples();
            if (numSamples > 0)
            {
                prop.get( samp, Alembic::Abc::ISampleSelector((Alembic::Abc::index_t)0) );
                arrayValues = AiArrayAllocate(samp->size(), numSamples, AI_TYPE_RGB);
                for( int i = 0; i < samp->size(); ++i)
                {
                    AtColor val;
                    val.r = (*samp)[i].x;
                    val.g = (*samp)[i].y;
                    val.b = (*samp)[i].z;
                    AiArraySetRGB(arrayValues,i, val);

                }
                AiNodeSetArray(node, header.getName().c_str(), arrayValues);
            }
        }
    }
    else if (Abc::IC4fArrayProperty::matches(header))
    {
        // color type + alpha
        Abc::C4fArraySamplePtr samp;
        Abc::IC4fArrayProperty prop(props, header.getName());
        if (prop.valid())
        {
            size_t numSamples = prop.getNumSamples();
            if (numSamples > 0)
            {
                prop.get( samp, Alembic::Abc::ISampleSelector((Alembic::Abc::index_t)0) );
                arrayValues = AiArrayAllocate(samp->size(), numSamples, AI_TYPE_RGBA);
                for( int i = 0; i < samp->size(); ++i)
                {
                    AtRGBA val;
                    
                    val.r = (*samp)[i].r;
                    val.g = (*samp)[i].g;
                    val.b = (*samp)[i].b;
                    val.a = (*samp)[i].a;
                    AiArraySetRGBA(arrayValues,i, val);

                }
                AiNodeSetArray(node, header.getName().c_str(), arrayValues);
            }
        }
    }
    else if (Abc::IP2fArrayProperty::matches(header))
    {
        //  point2
        Abc::P2fArraySamplePtr samp;
        Abc::IP2fArrayProperty prop(props, header.getName());
        if (prop.valid())
        {
            size_t numSamples = prop.getNumSamples();
            if (numSamples > 0)
            {
                prop.get( samp, Alembic::Abc::ISampleSelector((Alembic::Abc::index_t)0) );
                arrayValues = AiArrayAllocate(samp->size(), numSamples, AI_TYPE_POINT2);
                for( int i = 0; i < samp->size(); ++i)
                {
                    AtPoint2 val;
                    val.x = (*samp)[i].x;
                    val.y = (*samp)[i].y;
                    AiArraySetPnt2(arrayValues,i, val);

                }
                AiNodeSetArray(node, header.getName().c_str(), arrayValues);
            }
        }
    }

}

void setParameter(Alembic::Abc::ICompoundProperty props, Alembic::AbcCoreAbstract::PropertyHeader header, AtNode* node)
{
    if (Abc::IFloatProperty::matches(header))
    {
        // float type
        Abc::IFloatProperty prop(props, header.getName());
        if (prop.valid())
        {
            AiNodeSetFlt(node, header.getName().c_str(), prop.getValue());
            AiMsgDebug("Setting float parameter %s.%s with value %f", AiNodeGetName(node), header.getName().c_str(), prop.getValue());
        }
    }
    else if (Abc::IInt32Property::matches(header))
    {
        // int type
        Abc::IInt32Property prop(props, header.getName());
        if (prop.valid())
        {
            AiNodeSetInt(node, header.getName().c_str(), prop.getValue());
            AiMsgDebug("Setting int32 parameter %s.%s with value %i", AiNodeGetName(node), header.getName().c_str(), prop.getValue());
        }
    }
    else if (Abc::IUInt32Property::matches(header))
    {
        // int type
        Abc::IUInt32Property prop(props, header.getName());
        if (prop.valid())
        {
            Alembic::AbcCoreAbstract::MetaData md = prop.getMetaData();
            if(md.get("type") == "byte")
            {
                AiNodeSetByte(node, header.getName().c_str(), prop.getValue());
                AiMsgDebug("Setting Byte parameter %s.%s with value %i", AiNodeGetName(node), header.getName().c_str(), prop.getValue());
            }
            else
            {
                AiNodeSetUInt(node, header.getName().c_str(), prop.getValue());
                AiMsgDebug("Setting Uint32 parameter %s.%s with value %i", AiNodeGetName(node), header.getName().c_str(), prop.getValue());
            }

        }
    }
    else if (Abc::IBoolProperty::matches(header))
    {
        // bool type
        Abc::IBoolProperty prop(props, header.getName());
        if (prop.valid())
        {
            AiNodeSetBool(node, header.getName().c_str(), prop.getValue());
            AiMsgDebug("Setting bool parameter %s.%s with value %i", AiNodeGetName(node), header.getName().c_str(), prop.getValue());
        }
    }
    else if (Abc::IStringProperty::matches(header))
    {
        // string type
        Abc::IStringProperty prop(props, header.getName());
        if (prop.valid())
        {
            AiNodeSetStr(node, header.getName().c_str(), prop.getValue().c_str());
            AiMsgDebug("Setting string parameter %s.%s with value %s", AiNodeGetName(node), header.getName().c_str(), prop.getValue().c_str());
        }
    }

    else if (Abc::IV3fProperty::matches(header))
    {
        // vector type
        Abc::IV3fProperty prop(props, header.getName());
        if (prop.valid())
        {
            AiNodeSetVec(node, header.getName().c_str(), prop.getValue().x , prop.getValue().y, prop.getValue().z);
            AiMsgDebug("Setting vector parameter %s.%s with value %f %f %f", AiNodeGetName(node), header.getName().c_str(),prop.getValue().x , prop.getValue().y, prop.getValue().z);
        }
    }
    else if (Abc::IP3fProperty::matches(header))
    {
        // vector type
        Abc::IP3fProperty prop(props, header.getName());
        if (prop.valid())
        {
            AiNodeSetPnt(node, header.getName().c_str(), prop.getValue().x , prop.getValue().y, prop.getValue().z);
            AiMsgDebug("Setting point parameter %s.%s with value %f %f %f", AiNodeGetName(node), header.getName().c_str(),prop.getValue().x , prop.getValue().y, prop.getValue().z);
        }
    }

    else if (Abc::IC3fProperty::matches(header))
    {
        // color type
        Abc::IC3fProperty prop(props, header.getName());
        if (prop.valid())
        {
            AiNodeSetRGB(node, header.getName().c_str(), prop.getValue().x , prop.getValue().y, prop.getValue().z);
            AiMsgDebug("Setting color parameter %s.%s with value %f %f %f", AiNodeGetName(node), header.getName().c_str(),prop.getValue().x , prop.getValue().y, prop.getValue().z);
        }
    }
    else if (Abc::IC4fProperty::matches(header))
    {
        // color type
        Abc::IC4fProperty prop(props, header.getName());
        if (prop.valid())
        {
            AiNodeSetRGBA(node, header.getName().c_str(), prop.getValue().r , prop.getValue().g, prop.getValue().b, prop.getValue().a);
            AiMsgDebug("Setting color parameter %s.%s with value %f %f %f %f", AiNodeGetName(node), header.getName().c_str(),prop.getValue().r , prop.getValue().g, prop.getValue().b, prop.getValue().a);
        }
    }
    
    else if (Abc::IP2fProperty::matches(header))
    {
        //  point2
        Abc::IP2fProperty prop(props, header.getName());
        if (prop.valid())
        {
            AiNodeSetPnt2(node, header.getName().c_str(), prop.getValue().x , prop.getValue().y);
            AiMsgDebug("Setting point2 parameter %s.%s with value %f %f", AiNodeGetName(node), header.getName().c_str(), prop.getValue().x , prop.getValue().y);
        }
    }

}

